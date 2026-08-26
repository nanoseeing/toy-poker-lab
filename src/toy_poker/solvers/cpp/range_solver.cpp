#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

template <typename Storage>
class RangeSolverCoreT {
 public:
  RangeSolverCoreT(
      py::array_t<int32_t, py::array::c_style | py::array::forcecast> players,
      py::array_t<int32_t, py::array::c_style | py::array::forcecast> offsets,
      py::array_t<int32_t, py::array::c_style | py::array::forcecast> children,
      py::array_t<int32_t, py::array::c_style | py::array::forcecast> folders,
      py::array_t<double, py::array::c_style | py::array::forcecast> terminal_returns,
      py::array_t<double, py::array::c_style | py::array::forcecast> matched,
      py::array_t<double, py::array::c_style | py::array::forcecast> oop_probability,
      py::array_t<double, py::array::c_style | py::array::forcecast> ip_probability,
      py::array_t<double, py::array::c_style | py::array::forcecast> locked_strategy,
      std::string algorithm, double alpha, double beta, double gamma)
      : players_(copy_1d(players)),
        offsets_(copy_1d(offsets)),
        children_(copy_1d(children)),
        folders_(copy_1d(folders)),
        terminal_returns_(copy_flat(terminal_returns)),
        matched_(copy_1d(matched)),
        oop_probability_(copy_1d(oop_probability)),
        ip_probability_(copy_1d(ip_probability)),
        locked_strategy_(copy_flat(locked_strategy)),
        algorithm_(std::move(algorithm)),
        alpha_(alpha),
        beta_(beta),
        gamma_(gamma) {
    if (players_.empty() || offsets_.size() != players_.size() + 1) {
      throw std::invalid_argument("invalid public-tree arrays");
    }
    if (oop_probability_.size() != ip_probability_.size() ||
        oop_probability_.empty()) {
      throw std::invalid_argument("rank probability arrays must have equal size");
    }
    if (algorithm_ != "cfr_plus" && algorithm_ != "dcfr") {
      throw std::invalid_argument("algorithm must be cfr_plus or dcfr");
    }
    num_ranks_ = oop_probability_.size();
    num_slots_ = children_.size();
    if (locked_strategy_.size() != num_slots_ * num_ranks_) {
      throw std::invalid_argument("locked strategy must have shape [slots, ranks]");
    }
    regrets_.assign(num_slots_ * num_ranks_, 0.0);
    strategy_sum_.assign(num_slots_ * num_ranks_, 0.0);
    strategy_.assign(num_slots_ * num_ranks_, 0.0);
    max_actions_ = 1;
    for (std::size_t node = 0; node < players_.size(); ++node) {
      max_actions_ = std::max(
          max_actions_, static_cast<std::size_t>(offsets_[node + 1] - offsets_[node]));
    }
    max_depth_ = tree_depth(0);
    child_scratch_.assign(
        (max_depth_ + 1) * max_actions_ * num_ranks_, 0.0);
    oop_reach_scratch_.assign((max_depth_ + 2) * num_ranks_, 0.0);
    ip_reach_scratch_.assign((max_depth_ + 2) * num_ranks_, 0.0);
  }

  void run_until(int target_iteration) {
    if (target_iteration < iteration_) {
      throw std::invalid_argument("target iteration cannot move backwards");
    }
    py::gil_scoped_release release;
    std::vector<double> unit(num_ranks_, 1.0);
    std::vector<double> root_output(num_ranks_, 0.0);
    while (iteration_ < target_iteration) {
      ++iteration_;
      for (int updating_player : {0, 1}) {
        compute_strategy();
        cfr(
            0, updating_player, unit.data(), unit.data(), 0,
            root_output.data());
      }
      compute_strategy();
      if (algorithm_ == "dcfr") {
        const double ratio = static_cast<double>(iteration_ - 1) / iteration_;
        const double factor = std::pow(ratio, gamma_);
        for (Storage& value : strategy_sum_) {
          value = static_cast<Storage>(static_cast<double>(value) * factor);
        }
      }
      const double weight = algorithm_ == "cfr_plus" ? iteration_ : 1.0;
      accumulate_average(0, unit.data(), unit.data(), 0, weight);
    }
  }

  py::array_t<double> average_strategy() const {
    py::array_t<double> output(
        {static_cast<py::ssize_t>(num_slots_),
         static_cast<py::ssize_t>(num_ranks_)});
    auto out = output.mutable_unchecked<2>();
    for (std::size_t node = 0; node < players_.size(); ++node) {
      if (players_[node] < 0) continue;
      const std::size_t begin = offsets_[node];
      const std::size_t end = offsets_[node + 1];
      const double uniform = 1.0 / static_cast<double>(end - begin);
      for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
        double total = 0.0;
        for (std::size_t slot = begin; slot < end; ++slot) {
          total += strategy_sum_[index(slot, rank)];
        }
        for (std::size_t slot = begin; slot < end; ++slot) {
          out(slot, rank) = rank_locked(begin, rank)
              ? locked_strategy_[index(slot, rank)]
              : (total > 0.0
                    ? static_cast<double>(strategy_sum_[index(slot, rank)]) / total
                    : uniform);
        }
      }
    }
    return output;
  }

  int iteration() const { return iteration_; }

 private:
  template <typename T, int Flags>
  static std::vector<T> copy_1d(const py::array_t<T, Flags>& array) {
    auto info = array.request();
    if (info.ndim != 1) throw std::invalid_argument("expected a 1-D array");
    const auto* ptr = static_cast<const T*>(info.ptr);
    return std::vector<T>(ptr, ptr + info.size);
  }

  template <int Flags>
  static std::vector<double> copy_flat(const py::array_t<double, Flags>& array) {
    auto info = array.request();
    const auto* ptr = static_cast<const double*>(info.ptr);
    return std::vector<double>(ptr, ptr + info.size);
  }

  std::size_t index(std::size_t slot, std::size_t rank) const {
    return slot * num_ranks_ + rank;
  }

  bool rank_locked(std::size_t begin, std::size_t rank) const {
    return std::isfinite(locked_strategy_[index(begin, rank)]);
  }

  std::size_t tree_depth(std::size_t node) const {
    std::size_t depth = 0;
    for (std::size_t slot = offsets_[node]; slot < static_cast<std::size_t>(offsets_[node + 1]); ++slot) {
      depth = std::max(depth, static_cast<std::size_t>(1) + tree_depth(children_[slot]));
    }
    return depth;
  }

  double* child_buffer(std::size_t depth, std::size_t action) {
    return child_scratch_.data() +
        (depth * max_actions_ + action) * num_ranks_;
  }

  double* oop_reach_buffer(std::size_t depth) {
    return oop_reach_scratch_.data() + depth * num_ranks_;
  }

  double* ip_reach_buffer(std::size_t depth) {
    return ip_reach_scratch_.data() + depth * num_ranks_;
  }

  void compute_strategy() {
    for (std::size_t node = 0; node < players_.size(); ++node) {
      if (players_[node] < 0) continue;
      const std::size_t begin = offsets_[node];
      const std::size_t end = offsets_[node + 1];
      const double uniform = 1.0 / static_cast<double>(end - begin);
      for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
        if (rank_locked(begin, rank)) {
          for (std::size_t slot = begin; slot < end; ++slot) {
            strategy_[index(slot, rank)] = static_cast<Storage>(
                locked_strategy_[index(slot, rank)]);
          }
          continue;
        }
        double total = 0.0;
        for (std::size_t slot = begin; slot < end; ++slot) {
          total += std::max(static_cast<double>(regrets_[index(slot, rank)]), 0.0);
        }
        for (std::size_t slot = begin; slot < end; ++slot) {
          strategy_[index(slot, rank)] = static_cast<Storage>(total > 0.0
              ? std::max(static_cast<double>(regrets_[index(slot, rank)]), 0.0) / total
              : uniform);
        }
      }
    }
  }

  void terminal_values(
      std::size_t node, int updating_player, const double* opponent_reach,
      double* result) const {
    const auto& probabilities =
        updating_player == 0 ? oop_probability_ : ip_probability_;
    double total = 0.0;
    for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
      total += probabilities[rank] * opponent_reach[rank];
    }
    if (folders_[node] >= 0) {
      const double value = terminal_returns_[node * 2 + updating_player] * total;
      std::fill(result, result + num_ranks_, value);
      return;
    }
    const double wager = matched_[node];
    const double win = 1.0 + wager;
    const double lose = -wager;
    double lower = 0.0;
    for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
      const double equal = probabilities[rank] * opponent_reach[rank];
      const double higher = total - lower - equal;
      result[rank] = win * lower + 0.5 * equal + lose * higher;
      lower += equal;
    }
  }

  void cfr(
      std::size_t node, int updating_player, const double* oop_reach,
      const double* ip_reach, std::size_t depth, double* result) {
    const int player = players_[node];
    if (player < 0) {
      terminal_values(
          node, updating_player, updating_player == 0 ? oop_reach : ip_reach,
          result);
      return;
    }
    const std::size_t begin = offsets_[node];
    const std::size_t end = offsets_[node + 1];
    const std::size_t action_count = end - begin;
    for (std::size_t action = 0; action < action_count; ++action) {
      const std::size_t slot = begin + action;
      double* values = child_buffer(depth, action);
      if (player != updating_player) {
        if (player == 1) {
          double* next = oop_reach_buffer(depth + 1);
          for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
            next[rank] = oop_reach[rank] * strategy_[index(slot, rank)];
          }
          cfr(children_[slot], updating_player, next, ip_reach, depth + 1, values);
        } else {
          double* next = ip_reach_buffer(depth + 1);
          for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
            next[rank] = ip_reach[rank] * strategy_[index(slot, rank)];
          }
          cfr(children_[slot], updating_player, oop_reach, next, depth + 1, values);
        }
      } else {
        cfr(
            children_[slot], updating_player, oop_reach, ip_reach, depth + 1,
            values);
      }
    }
    std::fill(result, result + num_ranks_, 0.0);
    if (player == updating_player) {
      for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
        if (rank_locked(begin, rank)) continue;
        for (std::size_t action = 0; action < action_count; ++action) {
          const std::size_t slot = begin + action;
          result[rank] += strategy_[index(slot, rank)] *
                          child_buffer(depth, action)[rank];
        }
      }
      const double positive_factor = std::pow(iteration_, alpha_) /
          (std::pow(iteration_, alpha_) + 1.0);
      const double negative_factor = std::pow(iteration_, beta_) /
          (std::pow(iteration_, beta_) + 1.0);
      for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
        for (std::size_t action = 0; action < action_count; ++action) {
          const std::size_t slot = begin + action;
          Storage& stored_regret = regrets_[index(slot, rank)];
          double regret = static_cast<double>(stored_regret);
          const double delta = child_buffer(depth, action)[rank] - result[rank];
          if (algorithm_ == "cfr_plus") {
            regret = std::max(regret + delta, 0.0);
          } else {
            regret *= regret > 0.0 ? positive_factor : negative_factor;
            regret += delta;
          }
          stored_regret = static_cast<Storage>(regret);
        }
      }
      return;
    }
    for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
      for (std::size_t action = 0; action < action_count; ++action) {
        result[rank] += child_buffer(depth, action)[rank];
      }
    }
  }

  void accumulate_average(
      std::size_t node, const double* oop_reach, const double* ip_reach,
      std::size_t depth, double weight) {
    const int player = players_[node];
    if (player < 0) return;
    const std::size_t begin = offsets_[node];
    const std::size_t end = offsets_[node + 1];
    const double* own_reach = player == 1 ? oop_reach : ip_reach;
    for (std::size_t slot = begin; slot < end; ++slot) {
      for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
        const std::size_t position = index(slot, rank);
        strategy_sum_[position] = static_cast<Storage>(
            static_cast<double>(strategy_sum_[position]) +
            weight * own_reach[rank] * static_cast<double>(strategy_[position]));
      }
    }
    for (std::size_t slot = begin; slot < end; ++slot) {
      if (player == 1) {
        double* next = oop_reach_buffer(depth + 1);
        for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
          next[rank] = oop_reach[rank] * strategy_[index(slot, rank)];
        }
        accumulate_average(children_[slot], next, ip_reach, depth + 1, weight);
      } else {
        double* next = ip_reach_buffer(depth + 1);
        for (std::size_t rank = 0; rank < num_ranks_; ++rank) {
          next[rank] = ip_reach[rank] * strategy_[index(slot, rank)];
        }
        accumulate_average(children_[slot], oop_reach, next, depth + 1, weight);
      }
    }
  }

  std::vector<int32_t> players_, offsets_, children_, folders_;
  std::vector<double> terminal_returns_, matched_;
  std::vector<double> oop_probability_, ip_probability_;
  std::vector<double> locked_strategy_;
  std::vector<Storage> regrets_, strategy_sum_, strategy_;
  std::vector<double> child_scratch_, oop_reach_scratch_, ip_reach_scratch_;
  std::string algorithm_;
  double alpha_, beta_, gamma_;
  std::size_t num_ranks_ = 0;
  std::size_t num_slots_ = 0;
  std::size_t max_actions_ = 0;
  std::size_t max_depth_ = 0;
  int iteration_ = 0;
};

using RangeSolverCore = RangeSolverCoreT<double>;
using RangeSolverCoreFloat32 = RangeSolverCoreT<float>;

PYBIND11_MODULE(_range_solver_cpp, module) {
  module.doc() = "C++ range-vector CFR+/DCFR kernel";
  py::class_<RangeSolverCore>(module, "RangeSolverCore")
      .def(py::init<
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           std::string, double, double, double>())
      .def("run_until", &RangeSolverCore::run_until)
      .def("average_strategy", &RangeSolverCore::average_strategy)
      .def_property_readonly("iteration", &RangeSolverCore::iteration);
  py::class_<RangeSolverCoreFloat32>(module, "RangeSolverCoreFloat32")
      .def(py::init<
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<int32_t, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           py::array_t<double, py::array::c_style | py::array::forcecast>,
           std::string, double, double, double>())
      .def("run_until", &RangeSolverCoreFloat32::run_until)
      .def("average_strategy", &RangeSolverCoreFloat32::average_strategy)
      .def_property_readonly("iteration", &RangeSolverCoreFloat32::iteration);
}
