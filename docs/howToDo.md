# 把持推論の実行手順 (howToDo.md)

このドキュメントでは、GraspGen を使用して実際に把持推論を実行するための手順を説明します。

## 1. モデルチェックポイントのダウンロード

まず、学習済みのモデルをダウンロードします。

```bash
git clone https://huggingface.co/adithyamurali/GraspGenModels <path_to_models_repo>
```
※ `<path_to_models_repo>` は任意のローカルパスに置き換えてください。

## 2. Docker コンテナの起動

このリポジトリでは `docker/docker-compose.yml` から ROS1 用または ROS2 用のどちらか一方のサービスを起動します。

Compose ファイル:

- [docker/docker-compose.yml](/home/robo25/yamaguchi/graspGen/docker/docker-compose.yml)

サービス名:

- `graspgen_ros1`
- `graspgen_ros2`

### 2-1. ROS2 イメージのビルド

```bash
bash docker/build.sh ros2
```

### 2-2. ROS1 イメージのビルド

```bash
CURL_INSECURE=1 bash docker/build.sh ros1
```

`CURL_INSECURE=1` は自己署名証明書環境で必要な回避策です。通常環境では外してください。

### 2-3. ROS2 コンテナの起動

```bash
docker compose -f docker/docker-compose.yml up --build graspgen_ros2
```

### 2-4. ROS1 コンテナの起動

```bash
docker compose -f docker/docker-compose.yml up --build graspgen_ros1
```

実行後、対象コンテナ内のシェルに入ります。

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
   # graspgen:ros2 または graspgen:ros1 のコンテナIDを確認
   ```

2. **コンテナへの接続**:
   ```bash
   docker exec -it <コンテナID> bash
   ```

3. **環境読み込み**:
   ROS2 コンテナ:
   ```bash
   source /opt/ros/humble/setup.bash
   ```

   ROS1 コンテナ:
   ```bash
   source /opt/ros/noetic/setup.bash
   ```

4. **推論スクリプトの実行**:
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

再ランキング版を使う場合:

```bash
python3 scripts/ros_inference_advanced.py --ros-args --params-file pram/ros_inference_advanced.yaml
```

### E. HSR 用マスク点群生成ノード (ROS1 Noetic)

HSR 側では [scripts/ros_inference_advanced_HSR.py](/home/robo25/yamaguchi/graspGen/scripts/ros_inference_advanced_HSR.py) を使います。

```bash
source /opt/ros/noetic/setup.bash
python3 scripts/ros_inference_advanced_HSR.py \
  _pointcloud_topic:=/hsrb/head_rgbd_sensor/depth_registered/rectified_points \
  _mask_topic:=/sam/mask \
  _output_topic:=/object_pointcloud
```

主な ROS1 パラメータ:

- `~pointcloud_topic`
- `~mask_topic`
- `~output_topic`
- `~sync_slop`
- `~sync_queue_size`
- `~mask_threshold`

### F. HSR 用把持推論ノード (ROS1 Noetic)

HSR 側でマスク済み点群をそのまま受けて再ランキング付き推論を行う場合は
[scripts/ros_inference_advanced_ros1.py](/home/guch1/ssd_yamaguchi/HSR/graspGen/scripts/ros_inference_advanced_ros1.py)
を使います。

```bash
source /opt/ros/noetic/setup.bash
rosparam load pram/ros_inference_advanced_ros1.yaml /grasp_inference_node_advanced_ros1
python3 scripts/ros_inference_advanced_ros1.py \
  _scene_topic:=/hsrb/head_rgbd_sensor/depth_registered/rectified_points \
  _object_topic:=/object_pointcloud \
  _target_frame:=base_link
```

主な ROS1 パラメータ:

- `~scene_topic`
- `~object_topic`
- `~gripper_config`
- `~target_frame`
- `~tf_timeout_sec`
- `~grasp_confidence_threshold`
- `~collision_threshold`
- `~table_clearance_threshold`
- `~support_plane_axis`
- `~support_plane_percentile`
- `~min_centrality_threshold`
- `~approach_corridor_radius`
- `~approach_corridor_length`
- `~surface_alignment_k_neighbors`
- `~score_weight_confidence`
- `~score_weight_centrality`
- `~score_weight_clearance`
- `~score_weight_surface_alignment`


## 補足
- **マウントパスについて**: Docker Compose ではモデルディレクトリは `/models` にマウントされます。そのため、スクリプトの引数も `/models/...` から始まるパスを指定してください。
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
q
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


### graspgen入出力トピック名と設定箇所
- scene 入力: /camera/camera/depth/color/points
- object 入力: /yolov8_seg_node/result_cloud
- best grasp 出力: /grasp/best_pose
- marker 出力: /grasp_markers
定義箇所は scripts/ros_inference_advanced.py と launch/grasp_inference.launch.py

TF 名の指定は今は target_frame パラメータです。デフォルトは base_link \
指定している箇所は scripts/ros_inference_advanced.py の declare_parameter('target_frame', 'base_link') とlaunch側の launch/grasp_inference.launch.py \
実際の変換は lookup_transform(self.target_frame, source_frame, ...) で引いている．

実行コマンドは
```bash
python3 scripts/ros_inference_advanced.py --ros-args --params-file pram/ros_inference_advanced.yaml
```

launch を使うなら
```bash
python3 launch/grasp_inference.launch.py
```

設定ファイル
実行時パラメータは```pram/ros_inference_advanced.yaml```

主な設定項目:
- scene_topic
- object_topic
- gripper_config
- target_frame
- tf_timeout_sec
- grasp_confidence_threshold
- collision_threshold
- table_clearance_threshold
- support_plane_axis
- support_plane_percentile
- min_centrality_threshold
- approach_corridor_radius
- approach_corridor_length
- surface_alignment_k_neighbors
- score_weight_confidence
- score_weight_centrality
- score_weight_clearance
- score_weight_surface_alignment

入出力トピック \
GraspGen ROS2 ノードが使う topic はこれです。

入力:
- scene 点群: /camera/camera/depth/color/points
- object 点群: /yolov8_seg_node/result_cloud

出力:
- 最良把持姿勢: /grasp/best_pose
- 可視化マーカー: /grasp_markers

型:
- 入力: sensor_msgs/msg/PointCloud2
- /grasp/best_pose: geometry_msgs/msg/PoseStamped
- /grasp_markers: visualization_msgs/msg/MarkerArray

TF
TF は source_frame -> target_frame を引いて使う \
今の基準フレームは target_frame: base_link
- カメラ点群は msg.header.frame_id から base_link へ変換
- 推論後の grasp も base_link 基準で評価
- /grasp/best_pose も base_link で publish

TF 関連パラメータ:
- target_frame: base_link
- tf_timeout_sec: 0.2



#### 動作確認コマンド例

ROS2 側で確認:
```bash
ros2 topic list
ros2 topic echo /grasp/best_pose
ros2 topic echo /grasp_markers
ros2 param dump /grasp_inference_node_advanced
ros2 run tf2_ros tf2_echo base_link <camera_frame> #tf確認するなら
```

ROS1 側で確認:
```bash
rostopic list
rostopic echo /object_pointcloud
rostopic info /object_pointcloud
```

コンテナの起動状況:
```bash
docker compose -f docker/docker-compose.yml ps
docker ps
```
