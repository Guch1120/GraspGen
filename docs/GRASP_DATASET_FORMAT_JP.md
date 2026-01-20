# GraspGen 把持データセットフォーマット

バージョン: `v.1.0.0`

GraspGen は、データセットが以下のフォーマットであることを想定しています。

1. **データ分割 (Splits)**: オブジェクトは学習セットと検証/テストセットに分けられます。`*.txt` ファイルの各行には、uuid（Objaverse の場合）またはオブジェクトメッシュファイル (obj/stl) への相対パス（オブジェクトデータセットのルートからの相対パス）を記述します。学習とテストで同じオブジェクトを使用する場合は、両方のリストに含めてください。
```
path/to/splits/
    train.txt
    valid.txt
```

2. **把持データセット (Grasp Dataset)**: 把持データは別のディレクトリに保存されます。
```
path/to/grasp/data/
    *.json
```

把持データセット内の各 JSON ファイルには、以下の情報が含まれています。
```json
{
    "object": {
        "file": # オブジェクトデータセット内のオブジェクトアセットへの相対パス
        "scale": # 把持のサンプリングおよび評価が行われた際のオブジェクトメッシュのスケール
    }, 
    "grasps": {
        "transforms": # グリッパーのベースリンクの 4x4 同次変換行列
        "object_in_gripper": # 成功した把持と失敗した把持を区別するためのマスク
    }
}
```

JSON ファイルは Python で以下のようにロードできます。
```python
import json
import numpy as np
grasps_dict = json.load(open("/path/to/json/file", "r"))
object_file = grasps_dict["object"]["file"]
object_scale = grasps_dict["object"]["scale"]
grasps = np.array(grasps_dict["grasps"]["transforms"])
grasp_mask = np.array(grasps_dict["grasps"]["object_in_gripper"])
positive_grasps = grasps[grasp_mask]
negative_grasps = grasps[~grasp_mask]
```
