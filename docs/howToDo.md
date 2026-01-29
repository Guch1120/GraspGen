# 把持推論の実行手順 (howToDo.md)

このドキュメントでは、GraspGen を使用して実際に把持推論を実行するための手順を説明します。

## 1. モデルチェックポイントのダウンロード

まず、学習済みのモデルをダウンロードします。

```bash
git clone https://huggingface.co/adithyamurali/GraspGenModels <path_to_models_repo>
```
※ `<path_to_models_repo>` は任意のローカルパスに置き換えてください。

## 2. MeshCat サーバーの起動 (可視化用)

推論結果をブラウザで見るために、別のターミナルで MeshCat サーバーを起動します。

```bash
# pip install meshcat が必要です
meshcat-server
```
起動後、ブラウザで `http://localhost:7001` (または表示されたURL) を開いておきます。

## 3. Docker コンテナの起動

ダウンロードしたモデルをマウントして、Docker コンテナを起動します。

```bash
# プロジェクトルートで実行
docker compose -f docker/docker-compose.yml run --rm graspgen
```

## 4. 推論デモの実行

コンテナ内に入ったら、目的のデータ形式に合わせて以下のコマンドを実行します。

### A. オブジェクト点群 (JSON) の場合
```bash
python scripts/demo_object_pc.py \
    --sample_data_dir GraspGenModels/sample_data/real_object_pc \
    --gripper_config GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml
```

### B. オブジェクトメッシュ (OBJ, STL等) の場合
```bash
python scripts/demo_object_mesh.py \
    --mesh_file GraspGenModels/sample_data/meshes/box.obj \
    --gripper_config GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml
```

### C. シーン全体の点群の場合
```bash
python scripts/demo_scene_pc.py \
    --sample_data_dir GraspGenModels/sample_data/real_scene_pc \
    --gripper_config GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml
```

## 補足
- **グリッパーの変更**: `--gripper_config` の引数を `/GraspGenModels/checkpoints/` 内にある他の `.yml` ファイル（例: `graspgen_franka_panda.yml`）に変更することで、異なるロボットハンドでの推論が可能です。
- **詳細なオプション**: 各スクリプトに `--help` を付けて実行することで、閾値 (`--grasp_threshold`) や生成数 (`--num_grasps`) などの詳細設定を確認できます。
## 5. 実機導入へのステップ (RealSense + YOLOv8)

RealSense カメラと YOLOv8 を組み合わせて実機で把持を行うための推奨フローです。

### ステップ 1: ROS2 側でのデータ保存と検証
まずは、ROS2 で取得した 1 フレーム分のデータを JSON 形式で保存し、GraspGen で推論できるか確認します。

#### ROS2 ノード内での保存例 (Python)
```python
import json
import numpy as np

# YOLO の BB で切り出した物体点群 (Nx3)
# object_pc = ... (numpy array)

data = {
    "pc": object_pc.tolist(),
    "pc_color": np.zeros_like(object_pc).tolist() # 色情報がなければ 0 埋め
}

with open("test_input.json", "w") as f:
    json.dump(data, f)
```

#### GraspGen 側での単発テスト
保存した `test_input.json` を Docker から見える場所に配置し、手順 4-A と同様に実行します。

### ステップ 2: 実装のポイント
- **外れ値除去 (Outlier Removal):** 
  RealSense の点群はノイズが多いため、推論前に必ず `point_cloud_outlier_removal` を適用してください。
- **座標変換 (Eye-in-Hand):** 
  ハンドカメラの場合、出力される把持ポーズはカメラ座標系です。ロボットを動かすには、以下の変換が必要です。
  `T_base = T_hand_to_base * T_camera_to_hand * T_grasp_in_camera`

### ステップ 3: ROS2 サーバ化の構成案
推論が安定したら、GraspGen を ROS2 Action/Service サーバとして実装します。

1. **Recognition Node (Python/Docker):** 
   - RealSense 点群と YOLO の BB を受信。
   - `GraspGenSampler` を使って把持ポーズを計算。
   - 推論結果を `geometry_msgs/PoseArray` 等で返す。
2. **Control Node (MoveIt2):** 
   - 推論サーバを呼び出し、得られたポーズへ軌道計画・実行。
