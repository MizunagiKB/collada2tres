# Collada Scene converter for GodotEngine 2

Collada形式のファイルから、GodotEngine 2用のテキストリソースファイル(tscn)を生成します。

> Generate a "tscn" file for GodotEngine 2 from COLLADA file.


## Usage

```
collada2tres.py -i [dae filename] -o [tscn filename]

-h, --help            show this help message and exit
-i I_FILE, --input I_FILE
                      Input Collada filename
-m MATERIAL, --material MATERIAL
                      Material Filter
-o O_FILE, --output O_FILE
                      Output tres filename
-v, --verbose
--wo-morph            Without Mesh morph
--wo-skin             Without Mesh skin
```


### Known issues

* Material information is not propagated.
* Textures do not load.
* Animations do not load.


## collada_scene struct (memo)

* collada_scene
  * xml_dom
  * unit_name
  * unit_value
  * up_axis [UP_X|UP_Y|UP_Z]
  * dict_id
  * dict_ref_source
  * list_node
    * CNode
      * matrix
      * mtx34
      * xml_node_instance
      * attr_instance_url
      * attr_instance_name

      * CGeometry
        * CMesh
          * CMorph
            * method
            * CInput("MORPH_TARGET_0", "MORPH_WEIGHT_0")
              * src[]
              * dst[CGeometry]
      * CController
        * CSkin
          * list_vcount
          * list_v
          * CInput(JOINT_0, WEIGHT_0)
            * src
            * dst
              * CGeometry
                * CMesh
                  * attr_geometry_id
                  * attr_geometry_name
                  * attr_material
                  * list_vcount
                  * list_p
                  * CInput(VERTEX_0, NORMAL0, TEXCOORD_0, TEXCOORD_1)
                    * src[]
                    * dst[]
                  * CMorph
                    * method
                    * CInput("MORPH_TARGET_0", "MORPH_WEIGHT_0")
                      * src[]
                      * dst[CGeometry]

    dict_material[key]
        CMaterial(attr_id, attr_name)
