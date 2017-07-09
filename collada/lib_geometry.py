# -*- coding: utf-8 -*-
# ------------------------------------------------------------------ import(s)
import sys
import xml.dom.minidom

import collada.collada_type as co_type
import collada.collada_util as co_util

import collada.lib_controller


# ------------------------------------------------------------------- param(s)
# ------------------------------------------------------------------- class(s)
# ---------------------------------------------------------------- function(s)
# ============================================================================
def load_mesh(collada_scene, o_mesh, logger=None):

    for input_type in ("VERTEX_0", "NORMAL_0", "TEXCOORD_0", "TEXCOORD_1"):

        if input_type in o_mesh.dict_input:

            o_input = o_mesh.dict_input[input_type]
            o_input.dst = []
            o_input.src = co_util.get_source_array_ref(
                collada_scene,
                o_input.attr_source,
                logger
            )

            if o_input.src is None:
                logger.error("[load_mesh] input_type = %s", input_type)

    n_pos = 0
    stride_size = o_mesh.max_offset + 1

    for v_count in o_mesh.list_vcount:

        dict_work = {}
        for input_type in o_mesh.dict_input.keys():
            dict_work[input_type] = []

        for n in range(v_count):
            list_data = o_mesh.list_p[n_pos:n_pos + stride_size]

            for input_type, o_input in o_mesh.dict_input.items():

                ref_addr = list_data[o_input.attr_offset]

                if input_type in ("VERTEX_0", "NORMAL_0"):
                    dict_work[input_type].append(o_input.src[ref_addr * 3 + 0] *  1)
                    dict_work[input_type].append(o_input.src[ref_addr * 3 + 2] *  1)
                    dict_work[input_type].append(o_input.src[ref_addr * 3 + 1] * -1)
                elif input_type in ("TEXCOORD_0", "TEXCOORD_1"):
                    dict_work[input_type].append(      o_input.src[ref_addr * 2 + 0])
                    dict_work[input_type].append(1.0 - o_input.src[ref_addr * 2 + 1])

            n_pos += stride_size

        for input_type, o_input in o_mesh.dict_input.items():
            o_input.dst += dict_work[input_type]

    return True


# ============================================================================
def create_geometry(collada_scene, xml_node_geometry, logger=None):

    o_geometry = co_type.CGeometry(collada_scene)
    o_geometry.attr_geometry_id = xml_node_geometry.getAttribute("id")
    o_geometry.attr_geometry_name = xml_node_geometry.getAttribute("name")

    logger.debug(
        "geometry> id = %s, name = %s",
        o_geometry.attr_geometry_id,
        o_geometry.attr_geometry_name
    )

    for xml_node_mesh in xml_node_geometry.getElementsByTagName("mesh"):
        for xml_node_mesh_type in xml_node_mesh.childNodes:
            if xml_node_mesh_type.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                continue
            elif xml_node_mesh_type.tagName in ("triangles", "polylist"):
                attr_material = xml_node_mesh_type.getAttribute("material")
                attr_count = int(xml_node_mesh_type.getAttribute("count"))

                if collada_scene.o_argv.MATERIAL is not None:
                    if attr_material not in collada_scene.o_argv.MATERIAL:
                        continue

                #
                if attr_material in collada_scene.dict_material:
                    o_material = collada_scene.dict_material[attr_material]
                elif attr_material in collada_scene.bind_material:
                    o_material = collada_scene.bind_material[attr_material]
                else:
                    o_material = None
                    logger.critical(
                        "[create_geometry] material '%s' is not found",
                        attr_material
                    )

                    sys.exit()

                logger.debug(
                    "geometry>mesh>%s> material = %s",
                    xml_node_mesh_type.tagName,
                    attr_material
                )

                o_mesh = co_type.CMesh()
                o_mesh.attr_geometry_id = None
                o_mesh.attr_geometry_name = None
                o_mesh.attr_material = attr_material
                o_mesh.material_ridx = o_material.resource_ridx
                o_mesh.material_name = o_material.attr_name

                #
                if xml_node_mesh_type.tagName == "triangles":
                    o_mesh.list_vcount = [3] * attr_count

                for xml_node_face in xml_node_mesh_type.childNodes:
                    if xml_node_face.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                        continue
                    elif xml_node_face.tagName == "input":

                        o_input = co_type.CInput()
                        o_input.attr_semantic = xml_node_face.getAttribute("semantic")
                        o_input.attr_source = xml_node_face.getAttribute("source")
                        o_input.attr_offset = int(xml_node_face.getAttribute("offset"))
                        try:
                            o_input.attr_set = int(xml_node_face.getAttribute("set"))
                        except ValueError:
                            o_input.attr_set = 0

                        o_input.attr_semantic = o_input.attr_semantic + "_" + str(o_input.attr_set)

                        o_mesh.dict_input[o_input.attr_semantic] = o_input

                        if o_input.attr_offset > o_mesh.max_offset:
                            o_mesh.max_offset = o_input.attr_offset

                        o_mesh.dict_input[o_input.attr_semantic] = o_input

                    elif xml_node_face.tagName == "vcount":
                        o_mesh.list_vcount = [int(v) for v in xml_node_face.childNodes[0].data.split()]

                    elif xml_node_face.tagName == "p":
                        o_mesh.list_p = [int(v) for v in xml_node_face.childNodes[0].data.split()]

                load_mesh(
                    collada_scene,
                    o_mesh,
                    logger
                )

                o_geometry.list_mesh.append(o_mesh)

    # Seach Morph
    if "#" + o_geometry.attr_geometry_id in collada_scene.dict_ref_source:
        for xml_node_controller in collada_scene.dict_ref_source[ "#" + o_geometry.attr_geometry_id]:
            for xml_node in co_util.iter_xml_element_node(xml_node_controller):

                if xml_node.tagName == "morph":

                    o_morph = co_type.CMorph()
                    o_morph.method = xml_node.getAttribute("method")

                    if collada.lib_controller.load_morph(collada_scene, xml_node, o_morph, logger) is True:
                        o_geometry.o_morph = o_morph
                        logger.debug("[create_geometry] controller morph found")

    return o_geometry



# [EOF]
