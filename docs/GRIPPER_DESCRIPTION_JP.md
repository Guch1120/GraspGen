# GraspGen グリッパー記述

バージョン: `v.1.0.0`

グリッパーは一意の名前 "gripper_name" によって指定されます。これは学習スクリプトの引数として使用されるほか、設定ファイルのベース名にもなります。

各グリッパーには、以下の3つのアセットを定義する必要があります。
1. YAML設定ファイル `{gripper_name}.yaml`
2. Python設定ファイル `{gripper_name}.py`
3. グリッパー単体の URDF

### YAML設定ファイル

`{gripper_name}.yaml` には、データ生成および学習で使用される以下の主要な変数が含まれます。

- `width`: 開いた状態（最大関節角）における指の間の距離
- `depth`: z軸方向のグリッパーの範囲（ベースリンクフレームから TCP フレームまで）
- `transform_offset_from_asset_to_graspgen_convention`: アセットから GraspGen の規約に変換するためのオフセット。平行移動とクォータニオンのリストとして表現されます（例: `[[xyz],[xyzw]]`）。

当プロジェクトのグリッパー定義は、以下の図に示す規約に従います。アプローチ方向は正の Z 軸であり、グリッパーの指が閉じる方向は X 軸に沿っています。

<img src="../fig/graspgen_coordinate_convention.png" width="380" height="250" title="doc1">

使用するグリッパーが異なる規約を持っている場合は、`transform_offset_from_asset_to_graspgen_convention` 変数を使用して、この規約に合わせるようにしてください。元の URDF を修正する必要はありません。

データセットで提供されている3つのグリッパーモデル（吸引式、Robotiq 2f-140、Franka-Panda）にフレームを重ねた例を以下に示します。

<img src="../fig/graspgen_coordinate_convention_examples.png" width="500" height="250" title="doc2">

### Python設定ファイル
Python スクリプト `{gripper_name}.py` では、以下の変数および関数を定義する必要があります。

- クラス `GripperModel`: グリッパー URDF から、衝突用および可視化用のメッシュをどのようにロードするかを指定します。
- 関数 `load_control_points_for_visualization`: MeshCat での可視化に必要なコントロールポイントをロードします。
- 関数 `load_control_points`: 学習メトリクスの適用に必要なコントロールポイントをロードします。

オプション：
`get_transform_from_base_link_to_tool_tcp`:
この関数が指定されていない場合、`depth` 値に基づく固定の正の Z オフセットであるとみなされます。

この規約に関するフィードバックがある場合は、GitHub イシューを追加してください！
