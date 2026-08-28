# Study執筆ガイド

この文書は教材本文ではなく、Studyを追加・修正するときの執筆者向けガイドです。

## 用語と表記

- 正確な定訳があり、日本語の文献でも日本語表記の方が一般的な用語は日本語にします。例：情報集合、
  終端ノード、純粋戦略、混合戦略、行動戦略、最適反応、ゼロ和、定和、利得。
- 直訳が不自然な用語や、ポーカー・ソルバーの解説で英語の方が一般的な用語は英語のまま使います。
  例：off-path、reach、counterfactual regret、Exploitability、Node lock、range advantage。
- EV、EQ、EQR、MDF、SPR、CFRは、基礎文書の初出で正式名称を示し、以後は略語に統一します。
- `Fold equity`、`Equity denial`のように一まとまりで定着した複合用語は、単独のEQと区別して名称を保持します。
- Check、Bet、Call、Raise、Fold、All-inは、ゲームとStrategy Viewerのaction名に合わせます。
- range、hand、pot、stack、street、showdownなど、この教材とソルバーで定着している語は英語で統一します。
- UI label、設定key、ファイル名、数式中の変数名は実装どおりの表記を保持します。

## handとrank

プレイヤーに配られるものはhandです。rankはhandの強さを表す値として使います。

- AKQ型ゲーム：A、K、Qをhandと呼び、`A > K > Q`を勝敗判定として示します。
- 数値型ゲーム：`rank rのhand`、`rankが高いhand`のように書きます。
- 戦略表：handを行に並べる場合は`OOP hand`、数値を帯域でまとめる場合は`rank帯`とします。
- Strategy Viewer：実装上のhand識別子が`rank`である場合は、UI labelとしてそのまま記載できます。

## ルール表と構成

ルール表はstandard minimum raiseを既定とします。「アクション制約」には、Node lock、強制Check、Raise不可、
standard minimum raiseを使わない場合など、既定から外れる条件だけを記載します。

新しいStudyは[`zz_template.md`](zz_template.md)を使い、教材の通読順に追加する場合だけ`study_XX_...md`の
連番を付けます。

「導出方法」の先頭では、局面、手番、handまたはrank帯、比較するaction、結論を表で整理します。その後、
表と同じ順序で場合分けし、純粋actionの理由、混合戦略の無差別条件、EVの順に説明します。
