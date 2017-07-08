# -*- coding: utf-8 -*-
# ------------------------------------------------------------------ import(s)
import sys

import collada.collada_type as co_type
import collada.collada_util as co_util

import collada.lib_geometry


# ------------------------------------------------------------------- param(s)
# ------------------------------------------------------------------- class(s)
# ---------------------------------------------------------------- function(s)
# ============================================================================
def load_skin(collada_scene, xml_node_skin, o_skin, logger=None):

    xml_node_vertex_weights = xml_node_skin.getElementsByTagName("vertex_weights")[0]

    list_mtx44 = []
    o_skin.list_mtx44 = []

    #
    for xml_node in co_util.iter_xml_element_node(xml_node_vertex_weights):

        if xml_node.tagName == "input":

            o_input = co_type.CInput()
            o_input.attr_semantic = xml_node.getAttribute("semantic")
            o_input.attr_source = xml_node.getAttribute("source")
            try:
                o_input.attr_offset = int(xml_node.getAttribute("offset"))
            except:
                o_input.attr_offset = 0
            try:
                o_input.attr_set = int(xml_node.getAttribute("set"))
            except ValueError:
                o_input.attr_set = 0

            o_input.attr_semantic = o_input.attr_semantic + "_" + str(o_input.attr_set)

            if o_input.attr_offset > o_skin.max_offset:
                o_skin.max_offset = o_input.attr_offset

            if o_input.attr_semantic == "JOINT_0":
                xml_node_joints = xml_node_skin.getElementsByTagName("joints")[0]
                for xml_node_joints_input in co_util.iter_xml_tag_name(xml_node_joints, "input"):
                    if xml_node_joints_input.getAttribute("semantic") == "INV_BIND_MATRIX":
                        list_matrix = co_util.get_source_array_ref(
                            collada_scene,
                            xml_node_joints_input.getAttribute("source"),
                            logger
                        )

                        list_mtx44 = co_util.array_to_matrix44(list_matrix)

                        logger.debug("[load_skin] INV_BIND_MATRIX count(%d)", len(o_skin.list_mtx44))


            o_skin.dict_input[o_input.attr_semantic] = o_input

        elif xml_node.tagName == "vcount":
            o_skin.list_vcount = [int(v) for v in xml_node.childNodes[0].data.split()]
        elif xml_node.tagName == "v":
            o_skin.list_v = [int(v) for v in xml_node.childNodes[0].data.split()]

    #
    for input_type in ["JOINT_0", "WEIGHT_0"]:

        if input_type in o_skin.dict_input:

            o_input = o_skin.dict_input[input_type]

            if input_type == "JOINT_0":
                list_id = co_util.get_source_array_ref(
                    collada_scene,
                    o_input.attr_source,
                    logger
                )

                if list_id is None:
                    logger.error("[load_skin:1] input_type = %s", input_type)

                list_armature = co_util.get_armature_list(
                    collada_scene,
                    list_id,
                    logger
                )

                if list_armature is None:
                    logger.error("[load_skin:2] input_type = %s", input_type)

                o_input.dst = []
                o_input.src = []
                for attr_id in list_id:
                    for o_node_joint in list_armature:
                        if o_node_joint.attr_id == attr_id:
                            o_input.src.append(o_node_joint)

            else:
                o_input.dst = []
                o_input.src = co_util.get_source_array_ref(
                    collada_scene,
                    o_input.attr_source,
                    logger
                )

                if o_input.src is None:
                    logger.error("[load_skin] input_type = %s", input_type)

    n_pos = 0
    stride_size = o_skin.max_offset + 1

    for v_count in o_skin.list_vcount:

        dict_work = {}
        for input_type in o_skin.dict_input.keys():
            dict_work[input_type] = [0, 0, 0, 0]

        for n in range(v_count):
            list_data = o_skin.list_v[n_pos:n_pos + stride_size]

            for input_type, o_input in o_skin.dict_input.items():
                ref_addr = list_data[o_input.attr_offset]

                if input_type in ("JOINT_0",):
                    try:
                        dict_work[input_type][n] = o_input.src[ref_addr]
                        o_skin.list_mtx44.append(list_mtx44[ref_addr])
                    except IndexError:
                        logger.error("[load_skin] n = %d/4, ref_addr = %d/%d", n, ref_addr, len(o_input.src))
                        raise

                elif input_type in ("WEIGHT_0",):
                    dict_work[input_type][n] = o_input.src[ref_addr]

            n_pos += stride_size

        for input_type, o_input in o_skin.dict_input.items():
            o_input.dst.append(dict_work[input_type])

    return True


# ============================================================================
def load_morph(collada_scene, xml_node_morph, o_morph, logger=None):

    xml_node_targets = xml_node_morph.getElementsByTagName("targets")[0]

    for xml_node_input in co_util.iter_xml_element_node(xml_node_targets):

        if xml_node_input.tagName == "input":

            o_input = co_type.CInput()
            o_input.attr_semantic = xml_node_input.getAttribute("semantic")
            o_input.attr_source = xml_node_input.getAttribute("source")
            try:
                o_input.attr_offset = int(xml_node_input.getAttribute("offset"))
            except:
                o_input.attr_offset = 0
            try:
                o_input.attr_set = int(xml_node_input.getAttribute("set"))
            except ValueError:
                o_input.attr_set = 0

            o_input.attr_semantic = o_input.attr_semantic + "_" + str(o_input.attr_set)

            o_morph.dict_input[o_input.attr_semantic] = o_input

    #
    for input_type in ["MORPH_TARGET_0", "MORPH_WEIGHT_0"]:

        if input_type in o_morph.dict_input:

            o_input = o_morph.dict_input[input_type]
            o_input.work = []
            o_input.dst = []
            o_input.src = co_util.get_source_array_ref(
                collada_scene,
                o_input.attr_source,
                logger
            )

            if o_input.src is None:
                logger.error("[load_morph] input_type = %s", input_type)

            if input_type == "MORPH_TARGET_0":
                for geometry_name in o_input.src:

                    xml_node_geometry = collada_scene.dict_id[geometry_name]

                    o_geometry = collada.lib_geometry.create_geometry(
                        collada_scene,
                        xml_node_geometry,
                        logger
                    )

                    o_input.dst.append(o_geometry)

            if input_type == "MORPH_WEIGHT_0":
                for v in o_input.src:
                    o_input.dst.append(v)

    return True


# ============================================================================
def create_controller(collada_scene, xml_node_controller, logger=None):

    o_controller = co_type.CController()
    o_controller.attr_controller_id = xml_node_controller.getAttribute("id")
    o_controller.attr_controller_name = xml_node_controller.getAttribute("name")

    for xml_node in co_util.iter_xml_element_node(xml_node_controller):

        if xml_node.tagName == "skin":

            o_skin = co_type.CSkin()
            o_skin.attr_source = xml_node.getAttribute("source")
            o_skin.o_geometry = collada.lib_geometry.create_geometry(
                collada_scene,
                collada_scene.dict_id[o_skin.attr_source[1:]],
                logger
            )

            #

            if load_skin(collada_scene, xml_node, o_skin, logger) is True:

                o_controller.o_skin = o_skin

        elif xml_node.tagName == "morph":

            o_morph = co_type.CMorph()
            o_morph.method = xml_node.getAttribute("method")

            if load_morph(collada_scene, xml_node, o_morph, logger) is True:
                o_controller.o_morph = o_morph

        else:
            logger.error("[create_controller] Undefine xml node '%s'", xml_node.tagName)
            return None

    return o_controller

# ============================================================================
def load_library_controllers(collada_scene, xml_node_library, logger=None):

    for xml_node in xml_node_library.getElementsByTagName("controller"):

        attr_controller_id = xml_node.getAttribute("id")
        attr_controller_name = xml_node.getAttribute("name")

        collada_scene.dict_controller[attr_controller_id] = create_controller(
            collada_scene, xml_node, logger
        )



# [EOF]
