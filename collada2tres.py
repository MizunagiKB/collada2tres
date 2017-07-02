# -*- coding: utf-8 -*-
import sys
import xml.dom.minidom
import logging
import argparse

import jinja2

import collada_lib


LOGGING_FORMAT = "%(asctime)-15s %(levelname)8s %(message)s"


# ============================================================================
def remap_geometry(collada_item, dict_source_map, offset_map, list_vcount, list_p, o_logger):
    """Y軸以外が上向きの場合は、頂点配列の入れ替えが必要。
    """

    o_geometry = collada_lib.CColladaGeometory()

    b_enable_armature = False

    if len(collada_item.dict_armature) > 0:
        b_enable_armature = True

    o_logger.debug(dict_source_map.items())
    o_logger.debug(offset_map.get_source("VERTEX"))
    o_logger.debug(offset_map.get_source("NORMAL"))
    o_logger.debug(offset_map.get_source("TEXCOORD"))

    ary_v = collada_item.dict_source[dict_source_map[offset_map.get_source("VERTEX")]]
    list_v = []
    ary_n = collada_item.dict_source[offset_map.get_source("NORMAL")]
    list_n = []
    ary_t = collada_item.dict_source[offset_map.get_source("TEXCOORD")]
    list_t = []

    list_j = []
    list_w = []

    n_pos = 0
    stride_size = offset_map.get_stride_size()

    for v_count in list_vcount:

        temp_v = []
        temp_n = []
        temp_t = []

        temp_j = []
        temp_w = []

        for n in range(v_count):
            list_data = list_p[n_pos:n_pos + stride_size]
            v_ref = list_data[offset_map.get_offset("VERTEX")]
            n_ref = list_data[offset_map.get_offset("NORMAL")]
            t_ref = list_data[offset_map.get_offset("TEXCOORD")]

            if collada_item.up_axis == "Y_UPz":
                for n in range(3):
                    temp_v.append(ary_v[v_ref * 3 + n])
                    temp_n.append(ary_n[n_ref * 3 + n])
            else:
                for n, flip in ((0, 1), (2, 1), (1, -1)):
                    temp_v.append(ary_v[v_ref * 3 + n] * flip)
                    temp_n.append(ary_n[n_ref * 3 + n] * flip)

            if b_enable_armature is True:
                temp_j.append(collada_item.skin_j[v_ref])
                temp_w.append(collada_item.skin_w[v_ref])

            for n, flip in ((0, 0), (1, 1)):
                if flip == 0:
                    temp_t.append(ary_t[t_ref * 2 + n])
                else:
                    temp_t.append(1.0 - ary_t[t_ref * 2 + n])

            n_pos += stride_size

            o_geometry.mesh_virt_size += 1

        if collada_item.up_axis == "Y_UPz":
            list_v += temp_v
            list_n += temp_n
            list_t += temp_t
            if b_enable_armature is True:
                list_j += temp_j
                list_w += temp_w

        else:
            list_v += temp_v[0:3]
            list_v += temp_v[6:9]
            list_v += temp_v[3:6]

            list_n += temp_n[0:3]
            list_n += temp_n[6:9]
            list_n += temp_n[3:6]

            list_t += temp_t[0:2]
            list_t += temp_t[4:6]
            list_t += temp_t[2:4]

            if b_enable_armature is True:

                list_j += temp_j[0:1]
                list_j += temp_j[2:3]
                list_j += temp_j[1:2]

                list_w += temp_w[0:1]
                list_w += temp_w[2:3]
                list_w += temp_w[1:2]

    o_geometry.varray_virt = list_v
    o_geometry.varray_norm = list_n
    o_geometry.varray_tex1 = list_t

    if b_enable_armature is True:

        o_geometry.varray_j = []
        for j1 in list_j:
            for j in j1:
                o_geometry.varray_j.append(j)

        o_geometry.varray_w = []
        for w1 in list_w:
            for w in w1:
                o_geometry.varray_w.append(w)

    return o_geometry


# ============================================================================
def mesh_convert(o_argv, o_dom, o_logger, o_node_parent, collada_item, geometry_name, insert_list):

    #
    dict_source_map = {}
    for o_node in o_node_parent.getElementsByTagName("vertices"):
        attr_id = o_node.getAttribute("id")

        o_node_sub = o_node.getElementsByTagName("input")[0]
        attr_semantic = o_node_sub.getAttribute("semantic")
        attr_source = o_node_sub.getAttribute("source")[1:]
        dict_source_map[attr_id] = attr_source

    #
    for node_name in ("polylist", "triangles"):
        for o_node in o_node_parent.getElementsByTagName(node_name):

            attr_material = o_node.getAttribute("material")
            attr_count = int(o_node.getAttribute("count"))

            if o_argv.MATERIAL is not None:
                if attr_material not in o_argv.MATERIAL:
                    continue

            o_logger.info("%s material:%s", node_name, attr_material)

            #
            offset_map = collada_lib.create_offset_map(
                o_node,
                "input"
            )

            if node_name == "triangles":
                list_vcount = [3] * attr_count
            else:
                list_vcount = collada_lib.array_loader(
                    o_node, "vcount", o_logger
                )

            list_p = collada_lib.array_loader(
                o_node, "p", o_logger
            )

            o_geometry = remap_geometry(
                collada_item,
                dict_source_map,
                offset_map,
                list_vcount,
                list_p,
                o_logger
            )

            n_index = 1

            o_geometry.geometry_name = geometry_name
            o_geometry.material = attr_material
            o_geometry.material_index = n_index
            o_geometry.material_name = attr_material

            for dict_material in collada_item.list_material:
                if dict_material["id"] == attr_material:
                    o_geometry.material = attr_material
                    o_geometry.material_index = n_index
                    o_geometry.material_name = dict_material["name"]
                    break
                n_index += 1

            insert_list.append(o_geometry)

# ============================================================================
def parse_geometries(o_argv, o_dom, o_logger, o_node_parent, collada_item):

    for o_node in o_node_parent.getElementsByTagName("geometry"):
        attr_id = o_node.getAttribute("id")
        attr_name = o_node.getAttribute("name")

        o_logger.info("geometry id:%s name:%s", attr_id, attr_name)

        insert_list = insert_list = collada_item.list_geometry

        if collada_item.morph_targets_map is not None:

            ref_target = collada_item.morph_targets_map.get_source("MORPH_TARGET")
            ref_weight = collada_item.morph_targets_map.get_source("MORPH_WEIGHT")

            if attr_id in collada_item.dict_source_morph[ref_target]:
                if attr_id not in collada_item.dict_morph:
                    collada_item.list_morph_name.append(attr_name)

                collada_item.dict_morph[attr_name] = []
                insert_list = collada_item.dict_morph[attr_name]

        #
        for o_node_sub in o_node.getElementsByTagName("mesh"):

            o_logger.info("geometry>mesh")

            mesh_convert(
                o_argv,
                o_dom, o_logger,
                o_node_sub,
                collada_item,
                attr_name,
                insert_list
            )


# ============================================================================
def remap_contoller(collada_item, dict_source_map, offset_map, list_vcount, list_v, o_logger):

    o_logger.debug(dict_source_map.items())
    o_logger.debug(offset_map.get_source("JOINT"))
    o_logger.debug(offset_map.get_source("WEIGHT"))

    ary_j = collada_item.dict_source[offset_map.get_source("JOINT")]
    list_j = []
    ary_w = collada_item.dict_source[offset_map.get_source("WEIGHT")]
    list_w = []

    n_pos = 0
    stride_size = offset_map.get_stride_size()

    for v_count in list_vcount:

        temp_j = [0, 0, 0, 0]
        temp_w = [0, 0, 0, 0]

        if v_count > 4:
            o_logger.warn("vcount > 4")
        else:
            for n in range(v_count):
                list_data = list_v[n_pos:n_pos + stride_size]
                j_ref = list_data[offset_map.get_offset("JOINT")]
                w_ref = list_data[offset_map.get_offset("WEIGHT")]

                temp_j[n] = collada_item.dict_armature[ary_j[j_ref]]
                temp_w[n] = ary_w[w_ref]

                n_pos += stride_size

        list_j.append(temp_j)
        list_w.append(temp_w)

    collada_item.skin_j = list_j
    collada_item.skin_w = list_w


# ============================================================================
def skin_convert(o_jinja_env, o_dom, o_logger, o_node_parent, collada_item):

    #
    #for o_node in o_node_parent.getElementsByTagName("bind_shape_matrix"):
    #    pass

    for o_node in o_node_parent.getElementsByTagName("source"):
        attr_id = o_node.getAttribute("id")

        o_node_param = o_node.getElementsByTagName("param")[0]
        attr_param_name = o_node_param.getAttribute("name")
        attr_param_type = o_node_param.getAttribute("type")

        if attr_param_name == "JOINT":
            collada_item.dict_source_controllers[attr_id] = collada_lib.array_loader(
                o_node, "Name_array", o_logger
            )

        if attr_param_name == "WEIGHT":
            collada_item.dict_source_controllers[attr_id] = collada_lib.array_loader(
                o_node, "float_array", o_logger
            )

    #
    dict_source_map = {}
    for o_node in o_node_parent.getElementsByTagName("joints"):
        attr_id = o_node.getAttribute("id")

        o_node_input = o_node.getElementsByTagName("input")[0]
        attr_semantic = o_node_input.getAttribute("semantic")
        attr_source = o_node_input.getAttribute("source")[1:]
        dict_source_map[attr_id] = attr_source

    #
    for o_node in o_node_parent.getElementsByTagName("vertex_weights"):

        offset_map = collada_lib.create_offset_map(o_node, "input")

        list_vcount = collada_lib.array_loader(
            o_node, "vcount", o_logger
        )

        list_v = collada_lib.array_loader(
            o_node, "v", o_logger
        )

        remap_contoller(
            collada_item,
            dict_source_map,
            offset_map,
            list_vcount,
            list_v,
            o_logger
        )


# ============================================================================
def morph_convert(o_jinja_env, o_dom, o_logger, o_node_parent, collada_item):

    for o_node in o_node_parent.getElementsByTagName("source"):
        attr_id = o_node.getAttribute("id")

        o_param = o_node.getElementsByTagName("param")[0]
        attr_param_name = o_param.getAttribute("name")
        attr_param_type = o_param.getAttribute("type")

        o_logger.info("morph>source id:%s", attr_id)
        o_logger.info(
            "morph>source>param name:%s type:%s",
            attr_param_name,
            attr_param_type
        )

        if attr_param_name == "IDREF":
            collada_item.dict_source_morph[attr_id] = collada_lib.array_loader(
                o_node, "IDREF_array", o_logger
            )
            for ref in collada_item.dict_source_morph[attr_id]:
                o_logger.debug(ref)

        if attr_param_name == "MORPH_WEIGHT":
            collada_item.dict_source_morph[attr_id] = collada_lib.array_loader(
                o_node, "float_array", o_logger
            )

    #
    for o_node in o_node_parent.getElementsByTagName("targets"):

        collada_item.morph_targets_map = collada_lib.create_offset_map(o_node, "input")


# ============================================================================
def parse_controllers(o_jinja_env, o_dom, o_logger, o_node_parent, collada_item):

    for o_node in o_node_parent.getElementsByTagName("controller"):
        attr_id = o_node.getAttribute("id")
        attr_name = o_node.getAttribute("name")
        o_logger.info("controller id:%s name:%s", attr_id, attr_name)

        for o_node_sub in o_node.getElementsByTagName("skin"):
            skin_convert(o_jinja_env, o_dom, o_logger, o_node_sub, collada_item)

        for o_node_sub in o_node.getElementsByTagName("morph"):
            morph_convert(o_jinja_env, o_dom, o_logger, o_node_sub, collada_item)


# ============================================================================
def parse_visual_scenes(o_argv, o_dom, o_logger, o_node_parent, collada_item):

    dict_armature = {}

    for o_node in o_node_parent.getElementsByTagName("node"):
        attr_id = o_node.getAttribute("id")
        attr_type = o_node.getAttribute("type")

        if attr_type == "JOINT":
            for o_node_joint in o_node.getElementsByTagName("node"):
                attr_id = o_node_joint.getAttribute("id")
                attr_type = o_node_joint.getAttribute("type")

                if attr_type == "JOINT":
                    if attr_id not in dict_armature:
                        dict_armature[attr_id] = len(dict_armature)

                        o_logger.info("node id:%s type:%s", attr_id, attr_type)

    collada_item.dict_armature = dict_armature


# ============================================================================
def parse_materials(o_argv, o_dom, o_logger, o_node_parent, collada_item):

    list_material = []

    for o_node in o_node_parent.getElementsByTagName("material"):
        attr_id = o_node.getAttribute("id")
        attr_name = o_node.getAttribute("name")
        o_logger.info("material id:%s name:%s", attr_id, attr_name)

        o_node_material = o_node.getElementsByTagName("instance_effect")[0]
        attr_url = o_node_material.getAttribute("url")

        if o_argv.MATERIAL is not None:
            if attr_id in o_argv.MATERIAL:
                list_material.append(
                    {
                        "id": attr_id,
                        "name": attr_name
                    }
                )
        else:
            list_material.append(
                {
                    "id": attr_id,
                    "name": attr_name
                }
            )

    collada_item.list_material = list_material


# ============================================================================
def build_source_data(o_argv, o_dom, o_logger, collada_item):

    for o_node in o_dom.getElementsByTagName("source"):
        attr_id = o_node.getAttribute("id")
        attr_name = o_node.getAttribute("name")

        if attr_id is "":
            continue

        o_logger.debug("*>source id:%s name:%s", attr_id, attr_name)

        data_array = None
        for array_type in ("float_array", "IDREF_array", "Name_array"):
            data_array = collada_lib.array_loader(
                o_node, array_type, o_logger
            )
            if data_array is not None:
                collada_item.dict_source[attr_id] = data_array
                break

        if data_array is None:
            o_logger.error("source %s type error", name)

# ============================================================================
def parse(o_argv, o_dom, o_logger):

    collada_item = collada_lib.CColladaItem()

    # Check UP Axis

    o_node = o_dom.getElementsByTagName("asset")[0].getElementsByTagName("up_axis")[0]
    up_axis = o_node.childNodes[0].data.strip().upper()
    collada_item.up_axis = up_axis
    o_logger.info("asset up_axis:%s", up_axis)

    build_source_data(o_argv, o_dom, o_logger, collada_item)

    # Load library nodes

    for o_node in o_dom.getElementsByTagName("library_materials"):
        parse_materials(o_argv, o_dom, o_logger, o_node, collada_item)

    for o_node in o_dom.getElementsByTagName("library_visual_scenes"):
        parse_visual_scenes(o_argv, o_dom, o_logger, o_node, collada_item)

    for o_node in o_dom.getElementsByTagName("library_controllers"):
        parse_controllers(o_argv, o_dom, o_logger, o_node, collada_item)

    for o_node in o_dom.getElementsByTagName("library_geometries"):
        parse_geometries(o_argv, o_dom, o_logger, o_node, collada_item)

    return collada_item


# ============================================================================
def main():
    """ Entry
    """

    o_parser = argparse.ArgumentParser()
    o_parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        dest="I_FILE",
        help="Input Collada filename"
    )
    o_parser.add_argument(
        "-m", "--material",
        type=str,
        required=False,
        dest="MATERIAL",
        help="Material Filter"
    )
    o_parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        dest="O_FILE",
        help="Output tres filename"
    )
    o_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="VERBOSE",
        default=False,
        help=""
    )

    o_argv = o_parser.parse_args()

    if o_argv.MATERIAL is not None:
        o_argv.MATERIAL = o_argv.MATERIAL.split(",")

    logging.basicConfig(format=LOGGING_FORMAT)

    o_logger = logging.getLogger(__name__)
    if o_argv.VERBOSE is False:
        o_logger.setLevel(logging.ERROR)
    else:
        o_logger.setLevel(logging.DEBUG)

    o_dom = xml.dom.minidom.parse(o_argv.I_FILE)

    if o_dom.documentElement.tagName.strip() != "COLLADA":
        o_log.error("File type error.")

    o_jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("./templates")
    )

    collada_item = parse(o_argv, o_dom, o_logger)

    # export tres file

    with open(o_argv.O_FILE, "w") as h_writer:

        o_template = o_jinja_env.get_template("godot_tres.jinja2")
        h_writer.write(o_template.render())

        o_template = o_jinja_env.get_template("godot_tres_material.jinja2")
        h_writer.write(
            o_template.render(
                collada_item=collada_item
            )
        )

        o_template = o_jinja_env.get_template("godot_tres_mesh.jinja2")
        h_writer.write(
            o_template.render(
                name="collada_export",
                collada_item=collada_item
            )
        )


if __name__ == "__main__":
    main()



# [EOF]
