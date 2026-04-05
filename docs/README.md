<!-- <img src="../fig/cover.png" width="1000" height="250" title="readme1">  -->

<div align="center">
  <img src="../fig/cover.png" alt="GraspGen logo" width="800" style="margin-left:'auto' margin-right:'auto' display:'block'"/>
  <br>
  <br>
  <h1>GraspGen: 拡散モデルに基づく6自由度把持フレームワーク</h1>
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

GraspGen は、拡散モデルに基づく 6-DOF ロボット把持生成のためのモジュール型フレームワークです。次のような多様な条件にまたがって拡張できます。 \
1) **実機構成**: 3 種類の異なるグリッパー（産業用ピンチグリッパー、吸引）に対応。 
2) **観測条件**: 部分的な 3D 点群と完全な 3D 点群の両方に対して頑健。 
3) **タスク複雑度**: 単一物体把持からクラッタ環境での把持まで対応。また、生成された把持を採点して順位付けする把持ディスクリミネータ向けに、新規かつ高性能な on-generator 学習レシピも導入しています。 
GraspGen は、実機とシミュレーションの両方で従来手法を上回り（FetchBench 把持ベンチマークで SOTA、17% 改善）、かつ高効率（メモリ使用量 21 分の 1）でリアルタイム（TensorRT 前で 20 Hz）に動作します。 
このリポジトリでは、データ生成、データ形式、学習および推論のための基盤を公開しています。

<img src="../fig/radar.png" width="200" height="250" title="readme1"> <img src="../fig/3.gif" width="350" height="250" title="readme2"> <img src="../fig/2.gif" width="350" height="250" title="readme3"> <img src="../fig/1_fast.gif" width="300" height="250" title="readme4">

## 💡 目次

1. [リリースニュース](#release-news)
2. [今後の予定](#future-features)
3. [インストール](#installation)
   - [Docker](#installation-with-docker)
   - [pip](#installation-with-pip)
   - [uv](#installation-with-uv)
   - [Client-Server](#zmq-server)
   - [MCP](#mcp-llm-tool-calling)
4. [モデルチェックポイントのダウンロード](#download-checkpoints)
5. [推論デモ](#inference-demos)
6. [データセット](#dataset)
7. [既存データセットでの学習](#training-with-existing-datasets)
8. [独自データセット持ち込み BYOD](#training-and-data-generation)
9. [GraspGen のフォーマットと規約](#graspgen-conventions)
10. [GraspGen の LLM ツール呼び出し](#llm-tool-calling)
11. [Omniverse / USD 対応](#omniverse-and-usd-support)
12. [FAQ](#faq)
13. [ライセンス](#license)
14. [引用](#citation)
15. [お問い合わせ](#contact)

<a id="release-news"></a>

## リリースニュース

- [2026/03/03] LLM から GraspGen をツールとして呼び出すための MCP を追加しました。詳細は [../mcp/](../mcp/) を参照してください。
- [2026/03/03] アプリケーション側で GraspGen をインストールせずに利用できる、ZMQ ベースのサーバーを追加しました。詳細は [../client-server/](../client-server/) を参照してください。
- [2026/02/18] 論文が ICRA 2026 に採択されました。
- [2025/10/28] シーン点群に基づいて衝突している把持を除外する機能を追加しました。
- [2025/09/30] Isaac Lab ベースの把持データ生成を [GraspDataGen](https://github.com/NVlabs/GraspDataGen) パッケージとして公開しました（注: [吸引グリッパー向けデータ生成](../grasp_gen/dataset/suction.py) はこのリポジトリに含まれています）。
- [2025/07/16] 初回コードリリース。バージョン `1.0.0`。
- [2025/03/18] データセットを [Hugging Face](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen) で公開しました。
- [2025/03/18] [Intrinsic.ai](https://www.intrinsic.ai/blog/posts/intrinsic-and-nvidia-deepen-platform-integrations-for-intelligent-robotics) にモデルデプロイに関するブログ記事が掲載されました。

<details>
<summary>追加機能の詳細 1: MCP</summary>

MCP は Model Context Protocol の略で、LLM が外部ツールを呼び出すための共通インターフェースです。GraspGen では [../mcp/](../mcp/) に MCP サーバーが追加されており、Cursor や Claude Desktop などから把持生成をツールとして呼び出せます。

この MCP サーバー自体は重い推論を行わず、背後で動いている GraspGen の ZMQ サーバーへリクエストを中継します。つまり構成としては `LLM <-> MCP <-> ZMQ Server <-> GraspGen` です。利用できる主な機能は、メッシュからの把持生成、点群からの把持生成、可視化、サーバー状態確認、サーバー情報取得です。

研究コードを単体で触るだけでなく、エージェントや自動化ワークフローへ接続しやすくなった、というのがこの追加の意味です。

</details>

<details>
<summary>追加機能の詳細 2: ZMQ Server</summary>

ZMQ は ZeroMQ という軽量メッセージング基盤です。HTTP サーバーよりも薄く、プロセス間やマシン間でリクエストとレスポンスをやり取りするためによく使われます。

今回の追加では、GraspGen を GPU 上で常駐する推論サーバーとして起動し、別プロセスや別マシンのクライアントから点群を送って把持結果を受け取れるようになりました。実装は [../client-server/](../client-server/) と [../grasp_gen/serving/](../grasp_gen/serving/) にあります。サーバーが受け付ける主な操作は `health`、`metadata`、`infer` の 3 つです。

この構成により、ロボット制御側や外部アプリは PyTorch や CUDA を持たなくても、軽量なクライアントだけで GraspGen を利用できます。重い推論環境を 1 箇所にまとめられるのが利点です。

</details>

<details>
<summary>追加機能の詳細 3: uv ベースの推論セットアップ</summary>

`uv` は Python 環境構築と依存関係管理を高速に行うためのツールです。今回 README に追加された `uv` 手順と [../install_uv_pointnet.sh](../install_uv_pointnet.sh) により、推論用途でのセットアップが以前よりかなり軽くなりました。

特に「学習までは不要で、推論だけすぐ試したい」というケースに向いています。`.venv` の作成、依存関係導入、PointNet 拡張のインストールまでを短い手順で済ませられます。

アルゴリズムが変わったというより、導入の敷居を下げる改善です。ZMQ クライアントや MCP のような軽量側の利用とも相性が良いです。

</details>

<details>
<summary>追加機能の詳細 4: USD / Omniverse 対応</summary>

USD は Pixar 系の 3D シーン記述フォーマットで、Omniverse や Isaac Sim で広く使われています。GraspGen では [../scripts/convert_obj_to_usd.py](../scripts/convert_obj_to_usd.py) と [../scripts/save_grasps_to_usd.py](../scripts/save_grasps_to_usd.py) が追加され、メッシュを USD に変換したり、予測した把持姿勢を USD シーンへ書き戻したりできるようになりました。

把持結果は `/world/grasps` に姿勢 Xform として保存でき、必要であれば `/world/grasps_visualization` にワイヤーフレームも追加できます。これにより、把持結果を単なる数値配列ではなく、3D シーン資産として Omniverse / Isaac Sim 側に持ち込めます。

GraspGen の出力をシミュレータや 3D ツールに自然に接続しやすくなった、というのがこの変更の要点です。

</details>

<details>
<summary>追加機能の詳細 5: 推論インストール検証テスト</summary>

[../tests/test_inference_installation.py](../tests/test_inference_installation.py) が追加され、依存関係が正しく入っているか、モデル初期化と推論経路が最後まで通るかを自動で確認できるようになりました。

このテストは学習済み重みを使わず、ランダム重みのモデルで `pointnet` と `ptv3` の両方を初期化し、100 個の 4x4 把持行列が返ることまで確認します。つまり「インストールできた」だけでなく、「最低限の推論実行が本当に通る」ことを検証しています。

README の `uv` 手順と組み合わせると、環境構築後の確認方法が明確になった点が実務上かなり大きいです。

</details>

<a id="future-features"></a>

## 今後の予定

- ~~[Isaac Lab](https://isaac-sim.github.io/IsaacLab/main/index.html) ベースの対向グリッパー向けデータ生成リポジトリ（注: [吸引グリッパー向けデータ生成](../grasp_gen/dataset/suction.py) は既に公開済み）~~
- ~~衝突フィルタリングの実例~~
- ~~実データによるファインチューニング **[時間的制約により現在は未計画]**~~
- PTV3 バックボーンは、[依存関係の問題](https://github.com/Pointcept/PointTransformerV3/issues/159) により、現時点では Cuda 12.8 / Blackwell GPU で動作しません。Cuda 12.8 を使う場合は、解消されるまで PointNet++ バックボーンを利用してください。

<a id="installation"></a>

## インストール

用途に応じてインストール方法を選んでください。学習には **Docker** を推奨します。推論だけなら **uv** が最も簡単かつ高速です。LLM エージェントや遠隔ロボットクライアントから利用するために、GraspGen を単独サーバーとして動かしたい場合は [../client-server/README.md](../client-server/README.md) を参照してください。LLM から呼び出すための MCP も追加されています。

**✅ すべての方法で動作確認済みです。**

| 方法 | 用途 | 複雑さ | 速度 |
|--------|----------|------------|-------|
| **Docker** | 学習 + 推論 | ⭐⭐⭐ 学習向け推奨 | 低速 |
| **pip / uv** | 推論 | ⭐⭐ 推論向け推奨 | 高速 |
| **ZMQ Server** | リモート推論（クライアント側インストール不要） | ⭐ [../client-server/](../client-server/) を参照 | 高速 |
| **MCP** | LLM ツール呼び出し | ⭐ [../mcp/](../mcp/) を参照 | 高速 |

<a id="installation-with-docker"></a>

### Docker でインストール

```bash
git clone https://github.com/NVlabs/GraspGen.git && cd GraspGen
bash docker/build.sh # しばらく時間がかかります
```

<a id="installation-with-pip"></a>

### Conda / Python 仮想環境で pip インストール

**[任意]** conda 環境がまだない場合は、先に作成してください。

```bash
conda create -n GraspGen python=3.10 -y && conda activate GraspGen
```

**[任意]** PyTorch をまだ入れていない場合は、先にインストールしてください。

```bash
pip install torch==2.1.0 torchvision==0.16.0 torch-cluster torch-scatter -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
```

pip でインストールします。

```bash
# リポジトリのクローンとインストール
git clone https://github.com/NVlabs/GraspGen.git && cd GraspGen && pip install -e .

# PointNet 依存関係のインストール
./install_pointnet.sh
```

**注意:** `install_pointnet.sh` は CUDA 関連の環境変数を自動で処理します。CUDA ランタイムヘッダと C++ コンパイラが導入されていることを確認してください。必要であれば、以下のように手動実行もできます。

```bash
export CC=/usr/bin/g++ && export CXX=/usr/bin/g++ && export CUDAHOSTCXX=/usr/bin/g++ && export TORCH_CUDA_ARCH_LIST="8.6" && cd pointnet2_ops && pip install --no-build-isolation .
```

<a id="installation-with-uv"></a>

### uv でインストール

推論だけを行いたい場合は、uv によるセットアップを推奨します。

**[任意]** uv が未導入なら先にインストールしてください。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # もしくはターミナルを再起動
```

リポジトリをクローンしてセットアップします。

```bash
# リポジトリのクローンとセットアップ
git clone https://github.com/NVlabs/GraspGen.git && cd GraspGen

# Python 環境の作成と依存関係のインストール
uv python install 3.10 && uv venv --python 3.10 .venv && source .venv/bin/activate
uv pip install -e .

# PointNet 依存関係のインストール
./install_uv_pointnet.sh
```

インストール成功確認には次を実行してください。

```bash
python tests/test_inference_installation.py
```

<a id="zmq-server"></a>

### ZMQ Server

任意のクライアントから、フルスタックをインストールせずに問い合わせ可能な単独推論サーバーとして GraspGen を使う場合は、[../client-server/README.md](../client-server/README.md) を参照してください。

<a id="mcp-llm-tool-calling"></a>

### MCP

LLM から GraspGen をツールとして呼び出せるようにするには、[../mcp/README.md](../mcp/README.md) を参照してください。

<a id="download-checkpoints"></a>

## モデルチェックポイントのダウンロード

チェックポイントは [HuggingFace](https://huggingface.co/adithyamurali/GraspGenModels) から取得できます。

```bash
git clone https://huggingface.co/adithyamurali/GraspGenModels
```

<a id="inference-demos"></a>

## 推論デモ

実世界の点群上で把持予測を可視化するスクリプトを追加しています。サンプルデータはモデルリポジトリ内の `sample_data` フォルダにあります。使い方は各スクリプトの引数を参照してください。実機で使う上位 `k` 件の把持だけを表示したい場合は、`--return_topk` フラグを指定します（デフォルトは `k=100`）。別のグリッパーで可視化したい場合は、`--gripper_config` 引数を変更してください。

### 前提条件

1. **データセット:** 先に [モデルチェックポイントのダウンロード](#download-checkpoints) を行ってください。以下ではそのパスを `<path_to_models_repo>` とします。
2. **Docker:** 1 つ目の引数には、ローカルにクローンした GraspGen リポジトリのパスを指定します。モデルディレクトリは `--models` フラグで渡します。これらはコンテナ内でそれぞれ `/code` と `/models` にマウントされます。

```bash
# 推論のみを行う場合
bash docker/run.sh <path_to_graspgen_code> --models <path_to_models_repo>
```

### セグメント済みオブジェクト点群に対する把持予測

```bash
cd /code/ && python scripts/demo_object_pc.py --sample_data_dir /models/sample_data/real_object_pc --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

<img src="../fig/pc/1.png" width="240" height="200" title="objpc1"> <img src="../fig/pc/2.png" width="240" height="200" title="objpc2"> <img src="../fig/pc/3.png" width="240" height="200" title="objpc3"> <img src="../fig/pc/4.png" width="200" height="200" title="objpc4"> <img src="../fig/pc/5.png" width="240" height="200" title="objpc5"> <img src="../fig/pc/6.png" width="200" height="200" title="objpc6">

### オブジェクトメッシュに対する把持予測

`.obj`、`.stl`、`.ply`、および USD 形式（`.usd`、`.usda`、`.usdc`、`.usdz`）に対応しています。USD ファイルは [scene_synthesizer](https://github.com/NVlabs/scene_synthesizer) 経由で読み込まれます。

```bash
cd /code/ && python scripts/demo_object_mesh.py --mesh_file /models/sample_data/meshes/box.obj --mesh_scale 1.0 --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

USD の例:

```bash
cd /code/ && python scripts/demo_object_mesh.py --mesh_file /path/to/object.usd --mesh_scale 1.0 --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

**オブジェクト、grasps（姿勢）、grasps_visualization（ワイヤーフレーム）を含む USD を生成する方法:**  
GraspGen リポジトリのルートで、`.venv` を有効化した状態で次を実行します。必要に応じて `GRIPPER_CONFIG` と `GRASPS_OUTPUT_USD` を置き換えてください。出力 USD には `/world` 配下に、オブジェクトメッシュ、`/world/grasps`（姿勢 Xform のみ）、`/world/grasps_visualization`（viser と同形式のグリッパーワイヤーフレーム付き姿勢）が含まれます。

```bash
# 1) メッシュを USD に変換（オブジェクトのみ）
python scripts/convert_obj_to_usd.py --input assets/objects/box.obj --output assets/objects/box.usd

# 2) GraspGen 推論を実行して YAML に保存
python scripts/demo_object_mesh.py --mesh_file assets/objects/box.usd --mesh_scale 1.0 \
  --gripper_config GRIPPER_CONFIG --output_file /tmp/box_grasps.yml --no-visualization --num_grasps 50

# 3) USD に grasps と grasps_visualization を書き込む
python scripts/save_grasps_to_usd.py --usd_file assets/objects/box.usd --grasps_yaml /tmp/box_grasps.yml \
  --gripper_name robotiq_2f_140 --output GRASPS_OUTPUT_USD
```

Robotiq 用チェックポイントを使う例（`GRIPPER_CONFIG` には GraspGenModels のパス、たとえば `../GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml` を設定）:

```bash
python scripts/convert_obj_to_usd.py --input assets/objects/box.obj --output assets/objects/box.usd
python scripts/demo_object_mesh.py --mesh_file assets/objects/box.usd --mesh_scale 1.0 \
  --gripper_config ../GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml \
  --output_file /tmp/box_grasps.yml --no-visualization --num_grasps 50
python scripts/save_grasps_to_usd.py --usd_file assets/objects/box.usd --grasps_yaml /tmp/box_grasps.yml \
  --gripper_name robotiq_2f_140 --output assets/objects/box_with_grasps.usd
```

USD 内の箱を**薄い青色**にしたい場合は、変換時に `--light-blue` を追加してください。

```bash
python scripts/convert_obj_to_usd.py --input assets/objects/box.obj --output assets/objects/box.usd --light-blue
```

カスタム色（RGB 0-1）を使う場合は `--color 0.68 0.85 1.0` を指定します。

<img src="../fig/meshes/1.png" width="240" height="200" title="objpc1"> <img src="../fig/meshes/2.png" width="240" height="200" title="objpc2"> <img src="../fig/meshes/3.png" width="240" height="200" title="objpc3">

### **[高度な例]** シーン点群からの把持予測

```bash
cd /code/ && python scripts/demo_scene_pc.py --sample_data_dir /models/sample_data/real_scene_pc --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

<img src="../fig/pc/scene1.png" width="400" height="300" title="scenepc1"> <img src="../fig/pc/scene2.png" width="400" height="300" title="scenepc2">

### **[高度な例]** シーン点群からの衝突チェック付き把持予測

推論された把持を衝突に基づいて除外したい場合は、`--filter_collisions` フラグを使ってください。これは単純な点群ベースの衝突チェッカを用います。実機ロボットでは [NVBlox](https://github.com/NVlabs/nvblox_torch) の使用を推奨します。把持が衝突している場合は <span style="color:red">**赤**</span>、衝突していない場合は <span style="color:green">**緑**</span> で表示されます。深度画像とセグメンテーション画像をコマンドライン引数として与えて独自シーンを使いたい場合は、`../scripts/demo_collision_free_grasps.py` を参照してください。

```bash
cd /code/ && python scripts/demo_scene_pc.py --filter_collisions --sample_data_dir /models/sample_data/real_scene_pc --gripper_config /models/checkpoints/graspgen_franka_panda.yml
```

<img src="../fig/pc/collision1.png" width="400" height="300" title="collision1"> <img src="../fig/pc/collision2.png" width="400" height="300" title="collision2"> <img src="../fig/pc/collision3.png" width="400" height="300" title="collision3"> <img src="../fig/pc/collision4.png" width="400" height="300" title="collision4"> <img src="../fig/pc/collision5.png" width="400" height="300" title="collision5">

<small>注: このリポジトリの公開時点では、吸引グリッパー用チェックポイントは on-generator 学習で訓練されていないため、最良の把持スコアを出力しない可能性があります。</small>

<a id="dataset"></a>

## データセット

ダウンロード対象は 2 種類あります。

1. **把持データセット:** [HuggingFace](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen) からクローンできます。クローン先を `<path_to_grasp_dataset>` とします。

```bash
git clone https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GraspGen
```

2. **オブジェクトデータセット:** 下記のオブジェクトデータセットをダウンロードするための [スクリプト](../scripts/download_objects.py) を用意しています。`simplify` 引数の都合上、Docker コンテナ内で実行することを推奨します。保存先ディレクトリ `<path_to_object_dataset>` を指定してください。学習については簡略化メッシュ付きのみを検証しており（そのため `--simplify` が必要）、これはレンダリングとシミュレーション速度の向上に重要です。このスクリプトの完了には数時間かかる場合があり、CPU 使用量も高くなります。Docker 内で動かす場合は、保存先をマウントする必要があります。

まず Docker を起動します。

```bash
# データセットダウンロードのみを行う場合
mkdir -p <object_dataset>
bash docker/run.sh <path_to_graspgen_code> --grasp_dataset <path_to_grasp_dataset> --object_dataset <path_to_object_dataset>
```

```bash
cd /code && python scripts/download_objects.py --uuid_list /grasp_dataset/splits/franka_panda/ --output_dir /object_dataset --simplify
```

公開している把持データは合計 5,700 万件超です。[Objaverse XL](https://objaverse.allenai.org/)（LVIS）データセット中の 8,515 個のオブジェクト部分集合に対して計算されています。これらは Franka Panda、Robotiq-2f-140 産業用グリッパー、単一点接触吸引グリッパー（半径 30mm）の 3 種類に対応しています。

<img src="../fig/montage2.png" width="1000" height="500" title="readme2">

<a id="training-with-existing-datasets"></a>

## 既存データセットでの学習

この節では、3 種類のグリッパーに対して事前生成済みデータセットを使って学習する方法を説明します。独自データセット生成やゼロからの学習について詳しく知りたい場合は、[TUTORIAL_JP.md](TUTORIAL_JP.md) を参照してください。

### 前提条件

1. **データセット:** まず [データセット](#dataset) 節を参照し、把持データセットとオブジェクトデータセットをダウンロードしてください。
2. **パス設定:** 次のステップのために以下のパスを把握してください。

- `<path_to_graspgen_code>`: GraspGen リポジトリをクローンしたローカルパス
- `<path_to_grasp_dataset>`: 把持データセットをクローンしたローカルパス
- `<path_to_object_dataset>`: オブジェクトデータセットをダウンロードしたローカルパス
- `<path_to_results>`: 学習ログとキャッシュの保存先ローカルパス

3. **Docker:** 正しいパスを指定してコンテナを起動します。

```bash
# 学習のみを行う場合
mkdir -p <path_to_results>
bash docker/run.sh <path_to_graspgen_code> --grasp_dataset <path_to_grasp_dataset> --object_dataset <path_to_object_dataset> --results <path_to_results>
```

学習スクリプトは `runs/` にあります。各グリッパーについて、ジェネレータ（拡散モデル）とディスクリミネータを別々に学習します。

```bash
# ジェネレータ学習の例
cd /code && bash runs/train_graspgen_robotiq_2f_140_gen.sh

# ディスクリミネータ学習の例
cd /code && bash runs/train_graspgen_robotiq_2f_140_dis.sh
```

学習時の注意点:

- 論文の実験は 8 枚の A100 を搭載したマシンで実施しています。V100、A100、H100、L40s でも検証済みです。
- **データセットキャッシュ:** 実際の学習に入る前に、スクリプトはデータセットキャッシュを構築し、指定したキャッシュディレクトリに hdf5 `.h5` として保存します。キャッシュ構築と学習は、同一引数の `train_graspgen.py` で処理されます。キャッシュが存在しないか不完全な場合は、まずキャッシュを構築し、完了後に自動で学習へ進みます。キャッシュが既にある場合は、すぐに学習を開始します。
- **On-Generator 学習:** ディスクリミネータ学習向けの on-generator 学習は、まだ公開されていません。データ生成リポジトリ公開時にリリース予定です。これは予測把持の最良性能とスコアリングに必要です。

### 重要な学習引数

- `NGPU`: 学習に使う GPU 数
- `LOG_DIR`: TensorBoard ログ、チェックポイント、コンソールログの保存先
- `NWORKERS`: おおよそ `CPU コア数 / GPU 数` を目安に、0 でない値を設定
- `NUM_REDUNDANT_DATAPOINTS`: キャッシュ構築時のカメラ視点冗長性を制御する引数。大きいほどドメインランダム化と sim2real 転送に有利ですが、高すぎると `OOM` が発生します。デフォルトは 7 です。
- `debug` モード: 単一 GPU・1 ワーカーで実行するには `train.debug=True` を指定

### 学習のモニタリングと所要時間の目安

- **ジェネレータ:** 検証セット上の把持再構成誤差 `reconstruction/error_trans_l2` は数 `cm` 程度まで収束するはずです。収束には少なくとも 3,000 エポックが必要で、8 x A100 ノードでは約 40 時間かかります。
- **ディスクリミネータ:** 検証 AP スコアは 0.8 を超え、`bce_topk` 損失は低下するはずです。収束には少なくとも 3,000 エポックが必要で、8 x A100 ノードでは約 90 時間かかります。

<a id="training-and-data-generation"></a>

## 独自データセット持ち込み BYOD

把持データ生成を含む、ゼロからのモデル学習手順については [TUTORIAL_JP.md](TUTORIAL_JP.md) を参照してください。現時点では吸引グリッパーの例を同梱しています。ピンチグリッパー向けの Isaac Lab ベース把持データ生成については [GraspDataGen](https://github.com/NVlabs/GraspDataGen) パッケージを参照してください。

<a id="graspgen-conventions"></a>

## GraspGen のフォーマットと規約

採用しているフォーマットの詳細は次を参照してください。

- グリッパー設定: [GRIPPER_DESCRIPTION_JP.md](GRIPPER_DESCRIPTION_JP.md)
- 把持データセット形式: [GRASP_DATASET_FORMAT_JP.md](GRASP_DATASET_FORMAT_JP.md)

上記フォーマットに基づく Isaac Lab ベースの把持データ生成については、[GraspDataGen](https://github.com/NVlabs/GraspDataGen) を参照してください。

<a id="llm-tool-calling"></a>

## GraspGen の LLM ツール呼び出し

GraspGen は単独の ZMQ サーバーとしてデプロイできるため、モデルコードの import やローカル GPU を必要とせず、LLM エージェント、遠隔ロボットコントローラ、その他アプリケーションからツールとして呼び出せます。完全なドキュメント、プロトコル仕様、使用例は [../client-server/README.md](../client-server/README.md) を参照してください。

```bash
# サーバー起動（Docker）
bash docker/run_server.sh $(pwd) --models /path/to/GraspGenModels

# クライアントから呼び出し（Python。CUDA 不要）
python client-server/graspgen_client.py --mesh_file /path/to/mesh.obj --host localhost --port 5556
```

<a id="omniverse-and-usd-support"></a>

## Omniverse / USD 対応

GraspGen は推論入力として **USD** メッシュ（`.usd`、`.usda`、`.usdc`、`.usdz`）をサポートし、予測した把持を **Omniverse / Isaac Sim** 向けに USD へ書き戻すこともできます。1 つの USD には、オブジェクトメッシュ、**`/world/grasps`**（姿勢 Xform のみ）、**`/world/grasps_visualization`**（同じ姿勢 + グリッパーワイヤーフレーム）を含められます。メッシュ変換には [scene_synthesizer](https://github.com/NVlabs/scene_synthesizer) を使用します。以下はサンプルオブジェクト [../assets/objects/box.obj](../assets/objects/box.obj) を用いた例です。

```bash
# 1) OBJ → USD
python scripts/convert_obj_to_usd.py --input assets/objects/box.obj --output /tmp/box.usd

# 2) 推論を実行し、把持を YAML に保存
python scripts/demo_object_mesh.py --mesh_file /tmp/box.usd --mesh_scale 1.0 \
  --gripper_config GRIPPER_CONFIG --output_file /tmp/box_grasps.yml --no-visualization --num_grasps 50

# 3) grasps と grasps_visualization を USD に書き込み
python scripts/save_grasps_to_usd.py --usd_file assets/objects/box.usd --grasps_yaml /tmp/box_grasps.yml \
  --gripper_name robotiq_2f_140 --output assets/objects/box_with_grasps.usd
```

オプション: **`--wireframe_width W`**（デフォルト `0.001`）、**`--no_visualization`** でワイヤーフレーム描画を省略できます。ほかの形式（`.obj`、`.pcd` など）については [推論デモ](#inference-demos) を参照してください。

### Isaac Sim で把持を実行する（10 環境、Play で把持）

最大 10 個の環境を持つ **sim USD** を生成できます。各環境には、オブジェクト 1 個と予測把持姿勢に配置されたグリッパー 1 つが含まれます。この USD を **Omniverse / Isaac Sim** で開いて **Play** を押すと、グリッパーが閉じて対象を把持します。Robotiq 2F-85 グリッパー USD は `../assets/bots/robotiq_2f_85.usd` に含まれています（[GraspDataGen](https://github.com/NVlabs/GraspDataGen) からコピー）。

**1. 推論を実行して YAML を保存（最大 10 把持）**

```bash
python scripts/demo_object_mesh.py --mesh_file /tmp/box.usd --mesh_scale 1.0 \
  --gripper_config GRIPPER_CONFIG --output_file /tmp/box_grasps.yml --no-visualization --num_grasps 10
```

**2. sim USD を構築**（`box_with_grasps_sim.usd`）

```bash
python scripts/create_grasp_sim_usd.py --object_usd assets/objects/box.usd \
  --grasps_yaml /tmp/box_grasps.yml --output assets/objects/box_with_grasps_sim.usd --num_envs 10
```

**3. Isaac Sim で開き、把持スクリプトを実行**

- **Isaac Sim** の **File → Open** で `assets/objects/box_with_grasps_sim.usd` を開きます。
- **Play** を押してシミュレーションを開始します。
- **Window → Script Editor** で `scripts/run_grasp_sim_omniverse.py` を開いて実行します。  
  このスクリプトはコールバックを登録し、短い待機のあとでグリッパーを閉じる位置へ動かして把持させます。

`create_grasp_sim_usd.py` のオプション: **`--gripper_usd`**（デフォルト `assets/bots/robotiq_2f_85.usd`）、**`--num_envs`**（デフォルト `10`）、**`--env_spacing`**（デフォルト `0.6` m）。

<a id="faq"></a>

## FAQ

### 新しいグリッパー向けに学習するにはどうすればよいですか？

対象グリッパーについて、この[短いアンケート](https://docs.google.com/forms/d/e/1FAIpQLSdTCstEtaeZz5iSyjAhYFuJqSpMF671ftPylkS3ZJFhRIg3dg/viewform?usp=dialog) で教えてください。

新しいグリッパーで最適性能を得るには、指定された学習レシピで再学習することを推奨します。必要なものは次のとおりです。

- グリッパーの URDF。例は [../assets/](../assets/) を参照してください。
- GraspGen 形式のグリッパー記述。[GRIPPER_DESCRIPTION_JP.md](GRIPPER_DESCRIPTION_JP.md) を参照してください。
- 成功把持と失敗把持を含む、そのグリッパー向けの object-grasp データセット。[GRASP_DATASET_FORMAT_JP.md](GRASP_DATASET_FORMAT_JP.md) を参照してください。

把持データ生成を含むゼロからの学習手順は [TUTORIAL_JP.md](TUTORIAL_JP.md) を参照してください。データ生成自体は [GraspDataGen](https://github.com/NVlabs/GraspDataGen) も参照してください。

### 手元のグリッパーが既存グリッパーにかなり近いです。モデルを流用できますか？

多くの場合、物理特性が変わるため、そのグリッパー専用に再学習することを推奨します。

ただし、対向グリッパーで、既存のグリッパー（Franka / Robotiq）とストローク長が近い場合は、モデルの流用も可能です。両者のベースリンク座標系を合わせるために、z 方向のオフセット `import trimesh.transformations as tra; new_grasp = grasp @ tra.translation_matrix([0,0,-Z_OFFSET])` を適用する必要がある場合があります。

単一カップの吸引グリッパーを使っている場合は、30mm 吸着シール向けに学習された吸引モデルを流用できます。推論前に、オブジェクト点群またはメッシュ入力を `import trimesh.transformations as tra; mat = tra.scale_matrix(r/0.030)` でスケーリングしてください。ここで `r` は使用する吸引カップ半径です。

### 新しいオブジェクトデータセットでファインチューニングするにはどうすればよいですか？

GraspGen モデルは未知物体へのゼロショット汎化を意図して設計されています。新しい object/grasp データセットで追加学習したい、あるいはより大きなデータセットで学習したい場合は、1) 学習スクリプトの `train.checkpoint` に事前学習済みチェックポイントを渡し、2) 新しい grasp / object データセットへのパスに変更してください。規約は [GRASP_DATASET_FORMAT_JP.md](GRASP_DATASET_FORMAT_JP.md) を参照してください。

### 学習スクリプトが止まったり、エラーなしで kill されたりするのはなぜですか？

Docker コンテナに十分な CPU、スワップ、GPU メモリがあることを確認してください。それでも解決しない場合は GitHub Issue を作成してください。

### ロボット上で実行するにはどうすればよいですか？

このモデルをロボットで使うには、インスタンスセグメンテーション（例: [SAM2](https://ai.meta.com/sam2/)）とモーションプランニング（例: [cuRobo](https://curobo.org/)）が必要です。詳細は論文の実験セクションを参照してください。

### 欲しいグリッパーがデータセットに含まれていません

対象グリッパーをカバーできていない場合は、この[短いアンケート](https://docs.google.com/forms/d/e/1FAIpQLSdTCstEtaeZz5iSyjAhYFuJqSpMF671ftPylkS3ZJFhRIg3dg/viewform?usp=dialog) で情報提供してください。必要であれば URDF も添付できます。

### バグ報告や詳細な質問はどこで行えばよいですか？

GitHub Issue を作成してください。追って対応します。メールでの問い合わせでも構いません。

### コントリビュートできますか？

歓迎します。PR を送ってください。

<a id="license"></a>

## ライセンス

License Copyright © 2025, NVIDIA Corporation & affiliates. All rights reserved.

ビジネスに関する問い合わせは、[NVIDIA Research Licensing](https://www.nvidia.com/en-us/research/inquiries/) のフォームから送信してください。

<a id="citation"></a>

## 引用

この研究が有用だった場合は、以下の引用を検討してください。

```bibtex
@inproceedings{murali2025graspgen,
  title     = {GraspGen: A Diffusion-based Framework for 6-DOF Grasping with On-Generator Training},
  author    = {Murali, Adithyavairavan and Sundaralingam, Balakumar and Chao, Yu-Wei and Yamada, Jun and Yuan, Wentao and Carlson, Mark and Ramos, Fabio and Birchfield, Stan and Fox, Dieter and Eppner, Clemens},
  booktitle = {Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)},
  year      = {2026},
  publisher = {IEEE},
  url       = {https://arxiv.org/abs/2507.13097}
}
```

<a id="contact"></a>

## お問い合わせ

追加の問い合わせは [Adithya Murali](http://adithyamurali.com)（admurali@nvidia.com）まで連絡してください。
