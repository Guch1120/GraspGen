# 把持推論の実行手順 (howToDo.md)

このドキュメントでは、GraspGen を使用して実際に把持推論を実行するための手順を説明します。

## 1. モデルチェックポイントのダウンロード

まず、学習済みのモデルをダウンロードします。

```bash
git clone https://huggingface.co/adithyamurali/GraspGenModels <path_to_models_repo>
```
※ `<path_to_models_repo>` は任意のローカルパスに置き換えてください。

## 2. Docker コンテナの起動

ダウンロードしたモデルをマウントして、Docker コンテナを起動します。
プロジェクトルートで以下のコマンドを実行してください（`docker-compose` ではなく `run.sh` を使用します）。

```bash
# クローンした GraspGen のルートディレクトリで実行
# <path_to_models_repo> はモデルをクローンしたディレクトリへのパス
bash docker/run.sh . --models GraspGenModels/
```

実行後、コンテナ内のシェルに入ります。

## 3. MeshCat サーバーの起動 (可視化用)

コンテナに入ったら、まずは可視化用の MeshCat サーバーを起動します。

```bash
meshcat-server
```
起動後、ホスト側のブラウザで `http://localhost:7000` (または表示されたURL) を開いておきます。
**このターミナルは MeshCat サーバー専用としてそのままにしておきます。**

## 4. 推論デモの実行 (別ターミナル)

MeshCat サーバーを起動したまま、**別のターミナル**を開き、起動中のコンテナに入って推論を実行します。

1. **コンテナIDの確認**:
   ```bash
   docker ps
   # "graspgen:latest" イメージのコンテナID (例: a1b2c3d4e5) を確認
   ```

2. **コンテナへの接続**:
   ```bash
   docker exec -it <コンテナID> bash
   ```

3. **推論スクリプトの実行**:
   コンテナ内で以下のコマンドを実行します。

### A. オブジェクト点群 (JSON) の場合
```bash
python scripts/demo_object_pc.py \
    --sample_data_dir /models/sample_data/real_object_pc \
    --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

### B. オブジェクトメッシュ (OBJ, STL等) の場合
```bash
python scripts/demo_object_mesh.py \
    --mesh_file /models/sample_data/meshes/box.obj \
    --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

### C. シーン全体の点群の場合
```bash
python scripts/demo_scene_pc.py \
    --sample_data_dir /models/sample_data/real_scene_pc \
    --gripper_config /models/checkpoints/graspgen_robotiq_2f_140.yml
```

### D. 実機データでの推論 (RealSense + YOLOv8)
実機で取得した点群データトピックに対して推論を実行します。
```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=/code/fastdds_udp.xml
nano ~/.bashrc
# .bashrc に追加して読み込みまでしておくと今後楽
```
```bash
# 推論ノードの実行
python3 scripts/ros_inference.py --ros-args \
    -p scene_topic:=/camera/camera/depth/color/points \
    -p object_topic:=/yolov8_seg_node/result_cloud
```


## 補足
- **マウントパスについて**: `run.sh` を使用した場合、モデルディレクトリは `/models` にマウントされます。そのため、スクリプトの引数も `/models/...` から始まるパスを指定してください。
- **グリッパーの変更**: `--gripper_config` の引数を `/models/checkpoints/` 内にある他の `.yml` ファイル（例: `graspgen_franka_panda.yml`）に変更することで、異なるロボットハンドでの推論が可能です。
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
