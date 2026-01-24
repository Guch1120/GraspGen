<!-- <img src="../fig/cover.png" width="1000" height="250" title="readme1">  -->

<div align="center">
  <img src="../fig/cover.png" alt="GraspGen logo" width="800" style="margin-left:'auto' margin-right:'auto' display:'block'"/>
  <br>
  <br>
  <h1>GraspGen: 拡散モデルに基づく6自由度把持生成フレームワーク </h1>
</div>
<p align="center">
  <a href="https://graspgen.github.io">
    <img alt="Project Page" src="https://img.shields.io/badge/Project-Page-F0529C">
  </a>
  <a href="https://arxiv.org/abs/2507.13097">
    <img alt="Arxiv paper link" src="https://img.shields.io/badge/arxiv-2507.13097-blue">
  </a>
  <a href="https://huggingface.co/adithyamurali/GraspGenModels">
    <img alt="Model Checkpoints link" src="https://img.shields.io/badge/%F0%9F%A4%97%20HF-Models-yellow">
  </a>
  <a href="https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen">
    <img alt="Datasets link" src="https://img.shields.io/badge/%F0%9F%A4%97%20HF-Datasets-yellow">
  </a>
  <a href="https://www.youtube.com/watch?v=gM5fgK2aZ1Y&feature=youtu.be">
    <img alt="Video link" src="https://img.shields.io/badge/video-red">
  </a>
  <a href="https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen/blob/main/LICENSE_DATASET">
    <img alt="GitHub License" src="https://img.shields.io/badge/DATASET%20License-CC%20By%204.0-red.svg">
  </a>
</p>


GraspGenは、拡散モデル（Diffusion-based）を用いた6自由度のロボット把持（Grasp）生成のためのモジュール型フレームワークです。以下の3つの多様な設定においてスケーラビリティを備えています：1) **実施形態（Embodiments）** - 3つの異なるグリッパータイプ（産業用ピンチグリッパー、吸引式）に対応。2) **観測性（Observability）** - 部分的、または完全な3D点群に対する堅牢性。3) **複雑性（Complexity）** - 単一オブジェクトの把持から乱雑に置かれた（Clutter）環境での把持まで対応。また、生成された把持をスコアリングしてランク付けする「把持ディスクリミネータ（Grasp Discriminator）」のための、新しい高性能なオン・ジェネレータ（on-generator）学習レシピを導入しています。GraspGenは、性能（メモリ使用量21倍削減）とリアルタイム性（TensorRT前で20 Hz）を維持しつつ、シミュレーションおよび実環境の両方で従来手法を凌駕しています（FetchBench把持ベンチマークでSOTA、17%の改善）。このリポジトリでは、データ生成、データフォーマット、ならびに学習・推論のインフラを提供します。

**主な結果**


<img src="../fig/radar.png" width="200" height="250" title="readme1"> <img src="../fig/3.gif" width="350" height="250" title="readme2"> <img src="../fig/2.gif" width="350" height="250" title="readme3"> <img src="../fig/1_fast.gif" width="300" height="250" title="readme4">

## 💡 目次

1. [リリースニュース](#リリースニュース)
2. [今後の予定（ロードマップ）](#今後の予定ロードマップ)
3. [インストール](#インストール)
   - [Dockerでのインストール](#dockerでのインストール)
   - [Pipでのインストール](#pipでのインストール)
4. [モデルチェックポイントのダウンロード](#チェックポイントのダウンロード)
5. [推論デモ](#推論デモ)
6. [データセット](#データセット)
7. [既存データセットでの学習](#既存データセットでの学習)
8. [独自データセットの持ち込み (BYOD) - 新しいグリッパーとオブジェクトのための学習 + データ生成](#独自データセットの持ち込み-byod---新しいグリッパーとオブジェクトのための学習--データ生成)
9. [GraspGen フォーマットと規約](#graspgenの規約)
10. [FAQ（よくある質問）](#faq)
11. [ライセンス](#ライセンス)
12. [引用](#引用)
13. [お問い合わせ](#お問い合わせ)

## リリースニュース

- [2025/10/28] シーンの点群に基づいて衝突する把持を除外する機能を追加。

- [2025/09/30] Isaac-Lab ベースの把持データ生成が [GraspDataGen](https://github.com/NVlabs/GraspDataGen) パッケージとしてリリースされました（注：[吸引グリッパーのデータ生成はこのリポジトリに含まれています](../grasp_gen/dataset/suction.py)）。

- [2025/07/16] 初回コードリリース！バージョン `1.0.0`

- [2025/03/18] データセットを [Hugging Face](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen) でリリース！

- [2025/03/18] [Intrinsic.ai](https://www.intrinsic.ai/blog/posts/intrinsic-and-nvidia-deepen-platform-integrations-for-intelligent-robotics) でのモデルデプロイに関するブログ投稿。


## 今後の予定（ロードマップ）

- ~~[Isaac Lab](https://isaac-sim.github.io/IsaacLab/main/index.html) ベースのアンチポーダル（対向）グリッパー用データ生成リポジトリ（注：[吸引グリッパー用は既にリリース済み](../grasp_gen/dataset/suction.py)）~~
- ~~衝突フィルタリングの例~~
- ~~実データでのファインチューニング **[時間の都合により中止]**~~
- レイキャスティングに基づく把持幅の推定
- PTV3 バックボーンは、[依存関係の問題](https://github.com/Pointcept/PointTransformerV3/issues/159)により、まだ Cuda 12.8 では動作しません。Cuda 12.8 を使用する場合は、解決されるまで PointNet++ バックボーンを使用してください。

## インストール
学習には Docker でのインストールを推奨します。Pip でのインストールは推論のみテストされています。

### Dockerでのインストール
```bash
git clone https://github.com/NVlabs/GraspGen.git && cd GraspGen
bash docker/build.sh # これには時間がかかります
```

### Conda/Python仮想環境内でのPipインストール
**[任意]** もし conda 環境をまだ持っていない場合は、まず作成してください：
```bash
conda create -n GraspGen python=3.10 && conda activate GraspGen
```
**[任意]** pytorch がインストールされていない場合：
```bash
pip install torch==2.1.0 torchvision==0.16.0 torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
```
Pip でインストール：
```bash
# リポジトリをクローンしてインストール
git clone https://github.com/NVlabs/GraspGen.git
cd GraspGen && pip install -e .

# PointNet 依存関係のインストール
cd pointnet2_ops && pip install --no-build-isolation .

# その他の依存関係のインストール
pip install pyrender && pip install PyOpenGL==3.1.5 transformers tensordict pyrender diffusers==0.11.1 timm huggingface-hub==0.25.2 scene-synthesizer[recommend]
```

注意：`pointnet2_ops` をコンパイルする際、CUDA ランタイムヘッダーが見つからない、または C++ コンパイラがないなどの問題が発生した場合は、インストール前に以下を手動で設定してみてください：
```bash
export CC=/usr/bin/g++ && export CXX=/usr/bin/g++ && export CUDAHOSTCXX=/usr/bin/g++ && export TORCH_CUDA_ARCH_LIST="8.6"
```
## チェックポイントのダウンロード

チェックポイントは [HuggingFace](https://huggingface.co/adithyamurali/GraspGenModels) からダウンロードできます：
```
git clone https://huggingface.co/adithyamurali/GraspGenModels
```

## 推論デモ

モデルを使用して、実際の点群上で把持予測を可視化するためのスクリプトを追加しました。サンプルデータセットは、モデルリポジトリの `sample_data` フォルダにあります。使用方法についてはスクリプトの引数を確認してください。トップKの把持（実機で使用、デフォルトは `k=100`）のみをプロットするには、`--return_topk` フラグを渡してください。異なるグリッパーで可視化するには、`--gripper_config` 引数を変更してください。

### 前提条件

1. **データセット:** まず[チェックポイントをダウンロード](#チェックポイントのダウンロード)してください。これが以下の `<path_to_models_repo>` となります。
2. **MeshCat:** 以下の例はすべて、ブラウザ上の MeshCat で可視化されます。新しいターミナルで（任意の環境で `pip install meshcat` を実行後）次のコマンドを使用して MeshCat サーバーを起動できます：`meshcat-server`。また、専用の Docker コンテナをバックグラウンドで実行することもできます：`bash docker/run_meshcat.sh`。ブラウザで対応する URL（サーバー起動時に表示されます）にアクセスすると、結果が可視化されます。
3. **Docker:** 第1引数は、GraspGen リポジトリをローカルにクローンしたパスです（必須）。モデルディレクトリには `--models` フラグを使用してください。これらはコンテナ内の `/code` および `/models` パスにそれぞれマウントされます。
```bash
# 推論のみの場合
bash docker/run.sh <path_to_graspgen_code> --models <path_to_models_repo>
```

### セグメント化されたオブジェクト点群の把持予測

```bash
cd /code/ && python ../scripts/demo_object_pc.py --sample_data_dir /models/sample_data/real_object_pc --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```
<img src="../fig/pc/1.png" width="240" height="200" title="objpc1"> <img src="../fig/pc/2.png" width="240" height="200" title="objpc2"> <img src="../fig/pc/3.png" width="240" height="200" title="objpc3"> <img src="../fig/pc/4.png" width="200" height="200" title="objpc4"> <img src="../fig/pc/5.png" width="240" height="200" title="objpc5"> <img src="../fig/pc/6.png" width="200" height="200" title="objpc6">

### オブジェクトメッシュの把持予測
```bash
cd /code/ && python ../scripts/demo_object_mesh.py --mesh_file /models/sample_data/meshes/box.obj --mesh_scale 1.0 --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```
<img src="../fig/meshes/1.png" width="240" height="200" title="objpc1"> <img src="../fig/meshes/2.png" width="240" height="200" title="objpc2"> <img src="../fig/meshes/3.png" width="240" height="200" title="objpc3">

### **[高度な例]** シーン点群からのオブジェクト把持予測
```bash
cd /code/ && python ../scripts/demo_scene_pc.py --sample_data_dir /models/sample_data/real_scene_pc --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```
<img src="../fig/pc/scene1.png" width="400" height="300" title="scenepc1"> <img src="../fig/pc/scene2.png" width="400" height="300" title="scenepc2">

### **[高度な例]** シーン点群からの、衝突チェック付き把持予測
推論された把持を衝突に基づいてフィルタリングしたい場合は、`--filter_collisions` フラグを使用してください。これは単純な点群ベースの衝突チェッカーを使用します。実機ロボットでは、[NVBlox](https://github.com/NVlabs/nvblox_torch) の使用をお勧めします。把持が衝突している場合は <span style="color:red">**赤**</span>、衝突がない場合は <span style="color:green">**緑**</span> で表示されます。コマンドライン引数として深度画像とセグメンテーション画像を渡して独自のシーンを使用したい場合は、`../scripts/demo_collision_free_grasps.py` を参照してください。
```bash
cd /code/ && python ../scripts/demo_scene_pc.py --filter_collisions --sample_data_dir /models/sample_data/real_scene_pc --gripper_config /models/checkpoints/graspgen_franka_panda.yml
```
<img src="../fig/pc/collision1.png" width="400" height="300" title="collision1"> <img src="../fig/pc/collision2.png" width="400" height="300" title="collision2"> <img src="../fig/pc/collision3.png" width="400" height="300" title="collision3"> <img src="../fig/pc/collision4.png" width="400" height="300" title="collision4"> <img src="../fig/pc/collision5.png" width="400" height="300" title="collision5">

<!-- 衝突している把持（左）と衝突していない把持（右）の例を以下に示します。
<!-- <img src="fig/pc/collision4.png" width="400" height="300" title="collision4"> <img src="fig/pc/collision5.png" width="400" height="300" title="collision5"> -->

<small>注意：このリポジトリのリリース時点では、吸引グリッパーのチェックポイントはオン・ジェネレータ学習で訓練されていないため、最適な把持スコアを出力しない可能性があります。</small>

## データセット

ダウンロードすべき2つのデータセットがあります：
1. **把持データセット (Grasp Dataset)**: [HuggingFace](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen) からクローンできます。クローン先のパスが `<path_to_grasp_dataset>` となります。
```
git clone https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen
```
2. **オブジェクトデータセット (Object Dataset)**: オブジェクトデータセットをダウンロードするための[スクリプト](../scripts/download_objects.py)を用意しています。Docker コンテナ内での実行を推奨します（そうでないと `simplify` 引数が動作しません）。データセットを保存するディレクトリ `<path_to_object_dataset>` を指定する必要があります。レンダリングとシミュレーションの速度を向上させるために不可欠な、簡略化されたメッシュでの学習のみをテストしています（そのため `--simplify` 引数が必要です）。このスクリプトはダウンロード完了までに数時間かかる場合があり、CPU を大量に消費します。Docker コンテナ内で実行する場合は、このデータを保存する場所をマウントする必要があります。

まず Docker を起動します：
```bash
# データセットのダウンロードのみの場合
mkdir -p <object_dataset>
bash docker/run.sh <path_to_graspgen_code> --grasp_dataset <path_to_grasp_dataset> --object_dataset <path_to_object_dataset>
```

```bash
cd /code && python ../scripts/download_objects.py --uuid_list /grasp_dataset/splits/franka_panda/ --output_dir /object_dataset --simplify
```

合計で5,700万件以上の把持データを公開しています。これらは [Objaverse XL](https://objaverse.allenai.org/) (LVIS) データセットの8,515個のオブジェクトのサブセットに対して計算されたものです。これらの把持データは、Franka Panda、Robotiq-2f-140、および単一接触吸引グリッパー（半径30mm）の3種類のグリッパーに対応しています。

<img src="../fig/montage2.png" width="1000" height="500" title="readme2"> 

## 既存データセットでの学習

このセクションでは、3つのグリッパー用に生成済みの既存データセットでの学習について説明します。独自のデータセットの生成やモデルの学習に関するより詳細なチュートリアルについては、[../tutorials/TUTORIAL_JP.md](../tutorials/TUTORIAL_JP.md) を参照してください。

### 前提条件

1. **データセット:** まず[データセット](#データセット)セクションを参照し、把持およびオブジェクトデータセットをダウンロードしてください。
2. **パスの設定**: 次のステップのために、以下のパスを確認してください。
- `<path_to_graspgen_code>`: GraspGen リポジトリをクローンしたローカルパス
- `<path_to_grasp_dataset>`: 把持データセットをクローンしたローカルパス
- `<path_to_object_dataset>`: オブジェクトデータセットをダウンロードしたローカルパス
- `<path_to_results>`: 学習ログとキャッシュを保存するローカルパス
3. **Docker:** 正しいパスを指定して Docker コンテナを起動します：
```bash
# 学習のみの場合
mkdir -p <path_to_results>
bash docker/run.sh <path_to_graspgen_code> --grasp_dataset <path_to_grasp_dataset> --object_dataset <path_to_object_dataset> --results <path_to_results>
```

`../runs/` にある学習スクリプトを確認してください。グリッパーごとに、ジェネレータ（拡散モデル）とディスクリミネータを別々に学習させるモデルがあります。

```bash
# ジェネレータの学習例
cd /code && bash ../runs/train_graspgen_robotiq_2f_140_gen.sh

# ディスクリミネータの学習例
cd /code && bash ../runs/train_graspgen_robotiq_2f_140_dis.sh
```

学習に関する注意事項：
- 本論文の実験は8枚の A100 を搭載したマシンで実行されました。V100、A100、H100、L40s でテスト済みです。
- **データセットのキャッシュ:** 実際の学習を開始する前に、スクリプトはデータセットのキャッシュを構築し、指定されたキャッシュディレクトリに hdf5 `.h5` ファイルとして保存します。キャッシュ構築と学習の両方は、同じ引数を持つ `train_graspgen.py` スクリプトで処理されます。キャッシュが存在しないか不完全な場合、スクリプトはキャッシュを構築し、完了後に自動的に学習を続行します。キャッシュが既に存在する場合、スクリプトはすぐに学習を開始します。
- **オン・ジェネレータ学習:** ディスクリミネータの学習用のオン・ジェネレータ学習は（まだ）公開されていません。データ生成リポジトリのリリース時に公開される予定です。これは、予測された把持の最高のパフォーマンスとスコアリングのために必要です（論文参照）。

### 重要な学習引数
- `NGPU`: 学習に使用する GPU の数
- `LOG_DIR`: tensorboard のログ、チェックポイント、コンソールログの保存先
- `NWORKERS`: 目安として、`CPUコア数` / `GPU数` 前後のゼロでない数値を設定してください
- `NUM_REDUNDANT_DATAPOINTS`: キャッシュ構築時における（カメラ視点の）冗長性を制御します。この数値が高いほど、ドメインランダム化と sim2real 転送が向上します。デフォルトは7です。高すぎると `OOM` エラーが発生します。
- `debug` モード: 単一 GPU ジョブと1つのワーカーで実行するには、引数 `train.debug=True` を設定します。

### 学習のモニタリングと推定時間：
- **ジェネレータ**: 検証セットにおける把持再構成エラー `reconstruction/error_trans_l2` は、数 `cm` に収束する必要があります。収束には少なくとも3,000エポックかかります。8 X A100 ノードで、3,000エポックに約40時間かかります。
- **ディスクリミネータ**: 検証 AP スコアは0.8を超え、`bce_topk` 損失が減少する必要があります。収束には少なくとも3,000エポックかかります。8 X A100 ノードで、3,000エポックに約90時間かかります。

## 学習 & データ生成 (新しいオブジェクトとグリッパー用)

把持データの生成を含む、ゼロからのモデル学習の各ステップの詳細については、[../tutorials/TUTORIAL_JP.md](../tutorials/TUTORIAL_JP.md) を参照してください。現在は吸引グリッパーの例が含まれています。ピンチグリッパー用の Isaac Lab ベースの把持データ生成については、[GraspDataGen](https://github.com/NVlabs/GraspDataGen) パッケージを参照してください。

## GraspGenの規約

採用しているフォーマットについては、以下のドキュメントを参照してください：
- グリッパー構成: [GRIPPER_DESCRIPTION_JP.md](GRIPPER_DESCRIPTION_JP.md)
- 把持データセットフォーマット: [GRASP_DATASET_FORMAT_JP.md](GRASP_DATASET_FORMAT_JP.md)

上記フォーマットでの Isaac Lab ベースの把持データ生成については、[GraspDataGen](https://github.com/NVlabs/GraspDataGen) パッケージを参照してください。

## FAQ

### 新しいグリッパーで学習するにはどうすればよいですか？

興味のあるグリッパーについて、こちらの[簡単なアンケート](https://docs.google.com/forms/d/e/1FAIpQLSdTCstEtaeZz5iSyjAhYFuJqSpMF671ftPylkS3ZJFhRIg3dg/viewform?usp=dialog)でお知らせください。

新しいグリッパーで最適なパフォーマンスを得るには、指定の学習レシピでモデルを再学習させることをお勧めします。そのためには以下が必要です：

* グリッパーの URDF。例については [../assets/](../assets/) を参照してください。
* GraspGen フォーマットによるグリッパーの説明。[GRIPPER_DESCRIPTION_JP.md](GRIPPER_DESCRIPTION_JP.md) を参照してください。
* そのグリッパー用の、成功および失敗した把持からなるオブジェクト把持データセット。[GRASP_DATASET_FORMAT_JP.md](GRASP_DATASET_FORMAT_JP.md) を参照。

把持データの生成を含む、ゼロからのモデル学習の詳細については [../tutorials/TUTORIAL_JP.md](../tutorials/TUTORIAL_JP.md) を参照してください。データ生成については [GraspDataGen](https://github.com/NVlabs/GraspDataGen) を参照。

### 私のグリッパーは既存のグリッパーの1つと非常に似ています。モデルを転用（リターゲット）できますか？

ほとんどの場合、物理特性が変化しているため、各グリッパーに固有の新しいモデルを再学習させることをお勧めします。

グリッパーがアンチポーダル（対向）で、ストローク長（つまり幅）が既存のグリッパー（Franka/Robotiq）と似ている場合は、モデルを転用してみてください。両方のグリッパーのベースリンクフレームを合わせるために、z方向にオフセットを適用する必要があるかもしれません：`import trimesh.transformations as tra; new_grasp = grasp @ tra.translation_matrix([0,0,-Z_OFFSET])`。

単一カップの吸引グリッパーを使用している場合は、30mm吸引シール用に訓練された吸引モデルを転用できます。推論前にオブジェクト点群/メッシュ入力をリスケールすることができます：`import trimesh.transformations as tra; mat = tra.scale_matrix(r/0.030)`。ここで `r` は使用するグリッパーの吸引カップの半径です。


### 新しいオブジェクトデータセットでファインチューニングするにはどうすればよいですか？

GraspGen モデルは、未知のオブジェクトに対してゼロショットで汎化するように設計されています。新しいオブジェクトと把持のデータセットの組み合わせでモデルをさらにファインチューニングしたい、またはより大きなデータセットで学習したい場合は、1）学習スクリプトの `train.checkpoint` 引数に訓練済みチェックポイントを渡し、2）新しい把持/オブジェクトデータセットへのパスを変更する必要があります。[GRASP_DATASET_FORMAT_JP.md](GRASP_DATASET_FORMAT_JP.md) の規約を確認してください。

### 学習スクリプトが停止したり、エラーもなく強制終了したりするのはなぜですか？
Docker コンテナに十分な CPU、スワップ、および GPU メモリがあることを確認してください。解決しない場合は GitHub イシューを投稿してください。

### ロボットでこれを実行するにはどうすればよいですか？

このモデルを実行するには、インスタンスセグメンテーション（例：[SAM2](https://ai.meta.com/sam2/)）とモーションプランニング（例：[cuRobo](https://curobo.org/)）が必要です。詳細は論文の実験セクションを参照してください。

### 私が持っている/欲しいグリッパーがデータセットに含まれていません！
ご要望のグリッパーを網羅できておらず申し訳ありません。グリッパーの詳細を記載するために、このクイック[アンケート](https://docs.google.com/forms/d/e/1FAIpQLSdTCstEtaeZz5iSyjAhYFuJqSpMF671ftPylkS3ZJFhRIg3dg/viewform?usp=dialog)への回答を検討してください。任意で URDF を提供いただくことも可能です。

### バグの報告や詳細な質問はどうすればよいですか？
GitHub イシューを投稿してください。追って対応いたします！または、お気軽にメールでお問い合わせください。

### コントリビューション（貢献）について
コントリビューションは大歓迎です！プルリクエストを送信してください。

## ライセンス
License Copyright © 2025, NVIDIA Corporation & affiliates. All rights reserved.

ビジネスに関するお問い合わせは、[NVIDIA Research Licensing](https://www.nvidia.com/en-us/research/inquiries/) のフォームから送信してください。

## 引用

この研究が役立つ場合は、引用をご検討ください：

```
@article{murali2025graspgen,
  title={GraspGen: A Diffusion-based Framework for 6-DOF Grasping with On-Generator Training},
  author={Murali, Adithyavairavan and Sundaralingam, Balakumar and Chao, Yu-Wei and Yamada, Jun and Yuan, Wentao and Carlson, Mark and Ramos, Fabio and Birchfield, Stan and Fox, Dieter and Eppner, Clemens},
  journal={arXiv preprint arXiv:2507.13097},
  url={https://arxiv.org/abs/2507.13097},
  year={2025},
}
```

## お問い合わせ

詳細については、[Adithya Murali](http://adithyamurali.com) (admurali@nvidia.com) までお問い合わせください。
