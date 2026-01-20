# チュートリアル：単一オブジェクトに対する GraspGen モデルの学習

このチュートリアルでは、吸引カップグリッパーを使用して、単一のオブジェクトに対するデータセットの生成および GraspGen（ジェネレータとディスクリミネータ）モデルの学習を行う最小限の手順を示します。このチュートリアルでは、「オン・ジェネレータ学習」などの高度な概念は省略します。ここで学習したモデルは、同じオブジェクトの未知のポーズに対して一般化されますが、学習に使用した特定のオブジェクトに対して過学習（Overfit）気味になります。

## 📋 目次

1. [前提条件](#前提条件)
2. [ステップ 1: データセットの生成](#ステップ-1-データセットの生成)
3. [ステップ 2: ジェネレータモデルの学習](#ステップ-2-ジェネレータモデルの学習)
4. [ステップ 3: ディスクリミネータモデルの学習](#ステップ-3-ディスクリミネータモデルの学習)
5. [ステップ 4: 推論用のモデルチェックポイントの作成](#ステップ-4-推論用のモデルチェックポイントの作成)
6. [ステップ 5: 予測の可視化](#ステップ-5-予測の可視化)
7. [ワークフロー全体の実行例](#ワークフロー全体の実行例)
8. [ファイル構造](#ファイル構造)

## 前提条件

1. **Docker のセットアップ**: [メインの README](../README_JP.md) の前提条件に従って、学習に適した Docker コンテナを起動してください。[モデルチェックポイントのダウンロード](#チェックポイントのダウンロード)が完了していることを確認してください。このリポジトリ（`<path_to_models_repo>` に配置）には、本チュートリアルで使用するサンプルメッシュデータが含まれています。
   ```bash
   # 結果保存用ディレクトリの作成
   mkdir -p <path_to_results>
   
   # Docker コンテナの起動
   ./docker/run.sh <path_to_graspgen_code> --grasp_dataset <path_to_grasp_dataset> --object_dataset <path_to_object_dataset> --results <path_to_results> --models <path_to_models_repo> 
   ```

2. **オブジェクトメッシュ**: このチュートリアルでは `/models/sample_data/meshes/box.obj` を使用します。ただし、他の 3D メッシュファイル（`.obj`, `.stl` ファイル）を使用することも可能です。

## ステップ 1: データセットの生成

`generate_dataset_suction_single_object.py` スクリプトを使用して、単一オブジェクト用のデータセットを作成します。

### 基本的な使い方:
```bash
cd /code && python tutorials/generate_dataset_suction_single_object.py \
    --object_path /models/sample_data/meshes/box.obj \
    --object_scale 1.0 \
    --output_dir /results/tutorial \
    --no_visualization
```

### パラメータ:
- `--object_path`: オブジェクトメッシュファイルへのパス（必須）
- `--output_dir`: データセットを保存するディレクトリ（デフォルト: `/results/tutorial`）
- `--num_grasps`: 生成する把持の総数（デフォルト: 2000）
- `--object_scale`: オブジェクトのスケール係数（デフォルト: 1.0）
- `--gripper_config`: グリッパー設定ファイル（デフォルト: `single_suction_cup_30mm.yaml`）
- `--num_disturbances`: 評価用の外乱サンプルの数（デフォルト: 10）
- `--no_visualization`: 可視化を無効にする

### 出力:
スクリプトは以下のディレクトリ構造でデータセットを作成します。これは [GraspGen データセットフォーマット](../docs/GRASP_DATASET_FORMAT_JP.md)の規約に従っています。

```
/results/tutorial/
├── tutorial_object_dataset/
│   ├── <object_name>.obj
│   ├── train.txt
│   └── valid.txt
└── tutorial_grasp_dataset/
    └── <object_name>_grasps.json
```

## ステップ 2: ジェネレータモデルの学習

オブジェクトの把持ポーズを生成するための拡散モデルを学習させます。

### コマンド:
```bash
cd /code && bash tutorials/tutorial_train_gen.sh
```

### 期待される出力:
- `/results/tutorial/logs/single_suction_cup_30mm_gen_test/` に学習ログが保存される
- モデルチェックポイントが `last.pth` として保存される
- `/results/tutorial/cache/` にキャッシュファイルが生成される

### 学習のモニタリング:
- 最高のパフォーマンスを得るには、検証時の把持再構成エラー `reconstruction/error_trans_l2` が数 cm になる必要があります。
- この実行には、収束までに少なくとも 1,000 エポックかかる場合があります。ただし、大規模なオブジェクトデータセット（例：8,000 個のオブジェクトセット）の場合、収束には約 3,000〜5,000 エポックかかります。

## ステップ 3: ディスクリミネータモデルの学習

把持の質を評価するためのディスクリミネータモデルを学習させます。

### コマンド:
```bash
cd /code && bash tutorials/tutorial_train_dis.sh
```

### 期待される出力:
- `/results/tutorial/logs/single_suction_cup_30mm_dis_test/` に学習ログが保存される
- モデルチェックポイントが `last.pth` として保存される
- 最高のパフォーマンスを得るには、検証 AP スコアが 0.8 を超え、`bce_topk` 損失が減少する必要があります。

### 学習のモニタリング:
- 検証 AP スコアを確認してください（0.8 を超える必要があります）。
- この実行には、収束までに少なくとも 1,000 エポックかかる場合があります。ただし、より大規模なオブジェクトデータセット（例：8,000 個のオブジェクトセット）の場合、収束には約 3,000〜5,000 エポックかかります。
- 異なる把持タイプ（pos, neg, freespace, onpolicy）の損失をモニタリングしてください。
- すべての損失曲線が減少していることを確認してください。

## ステップ 4: 推論用の最終モデル設定ファイルの作成

両方のモデルの学習が完了したら、推論用の標準化されたチェックポイントを作成します。

### コマンド:
```bash
cd /code && python tutorials/generate_model_inference_config.py \
    --gen_log_dir /results/tutorial/logs/single_suction_cup_30mm_gen_test \
    --dis_log_dir /results/tutorial/logs/single_suction_cup_30mm_dis_test
```

### 期待される出力:
- モデルディレクトリ: `/results/tutorial/models/`
- ジェネレータチェックポイント: `gen.pth`
- ディスクリミネータチェックポイント: `dis.pth`


## ステップ 5: 予測の可視化

学習済みモデルを使用して、サンプルオブジェクトメッシュ上での把持予測を可視化します。

### コマンド:
```bash
cd /code && python scripts/demo_object_mesh.py \
    --mesh_file /models/sample_data/meshes/box.obj \
    --mesh_scale 1.0 \
    --gripper_config /results/tutorial/models/tutorial_model_config.yaml
```

### パラメータ:
- `--mesh_file`: オブジェクトメッシュファイルへのパス（例として同じ box.obj を使用）
- `--mesh_scale`: オブジェクトメッシュのスケール係数（デフォルト: 1.0）
- `--gripper_config`: ステップ 4 で作成した設定ファイルへのパス（デフォルト: `/results/tutorial/models/tutorial_model_config.yaml`）

### 期待される出力:
- オブジェクトメッシュを表示するインタラクティブな 3D 可視化
- オブジェクト上に重ねて表示される生成された把持ポーズ
- 色分けされた把持品質スコア
- 最良の把持が強調表示される

## ワークフロー全体の実行例

マグカップオブジェクトで学習させる場合の完全な例：

```bash
# 1. データセットの生成
cd /code && python tutorials/generate_dataset_suction_single_object.py \
    --object_path /path/to/mug.obj \
    --output_dir /results/tutorial \
    --num_grasps 2000 \
    --object_scale 1.0

# 2. ジェネレータの学習
cd /code && bash tutorials/tutorial_gen.sh

# 3. ディスクリミネータの学習
cd /code && bash tutorials/tutorial_dis.sh

# 4. 推論用のモデルチェックポイントの作成
cd /code && python tutorials/create_model_checkpoints_for_inference.py \
    --gen_log_dir /results/tutorial/logs/single_suction_cup_30mm_gen_test \
    --dis_log_dir /results/tutorial/logs/single_suction_cup_30mm_dis_test

# 5. 予測の可視化
cd /code && python scripts/demo_object_mesh.py \
    --mesh_file /models/sample_data/meshes/box.obj \
    --mesh_scale 1.0 \
    --gripper_config /results/tutorial/models/tutorial_model_config.yaml
```

## ファイル構造

すべてのスクリプトを実行すると、以下のようになります：
```
/results/tutorial/
├── tutorial_object_dataset/
│   ├── mug.obj
│   ├── train.txt
│   └── valid.txt
├── tutorial_grasp_dataset/
│   └── mug_grasps.json
├── logs/
│   ├── single_suction_cup_30mm_gen_test/
│   │   ├── last.pth
│   │   └── training_logs/
│   └── single_suction_cup_30mm_dis_test/
│       ├── last.pth
│       └── training_logs/
├── models/
│   ├── gen.pth
│   ├── dis.pth
│   └── tutorial_model_config.yaml
└── cache/
    └── tutorial_object_dataset/
       ├── cache_train_meshandpc_gen.h5
       └── cache_valid_meshandpc_gen.h5
```
