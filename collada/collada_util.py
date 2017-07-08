# -*- coding: utf-8 -*-
# ------------------------------------------------------------------ import(s)
import sys
import xml.dom.minidom
import numpy

import collada.collada_type as co_type


# ------------------------------------------------------------------- param(s)
# ------------------------------------------------------------------- class(s)

# ---------------------------------------------------------------- function(s)
# ============================================================================
def convert_mtx44_to_mtx34(mtx44):

    return [
        mtx44[ 0], mtx44[ 4], mtx44[ 8],
        mtx44[ 1], mtx44[ 5], mtx44[ 9],
        mtx44[ 2], mtx44[ 6], mtx44[10],
        mtx44[ 3], mtx44[11], mtx44[ 7] * -1
    ]


# ============================================================================
def mul_mtx44(m44a, m44b):

    nm44a = numpy.matrix(
        [
            m44a[ 0: 4],
            m44a[ 4: 8],
            m44a[ 8:12],
            m44a[12:16],
        ]
    )

    nm44b = numpy.matrix(
        [
            m44b[ 0: 4],
            m44b[ 4: 8],
            m44b[ 8:12],
            m44b[12:16],
        ]
    )

    mtx44 = nm44a.reshape(-1,).tolist()[0]

    return [
        mtx44[ 0], mtx44[ 4], mtx44[ 8],
        mtx44[ 1], mtx44[ 5], mtx44[ 9],
        mtx44[ 2], mtx44[ 6], mtx44[10],
        mtx44[ 3], mtx44[11], mtx44[ 7] * -1
    ]



# ============================================================================
def get_matrix44(xml_node, logger=None):

    if xml_node.tagName == "matrix":
        m44 = [float(v) for v in xml_node.childNodes[0].data.split()]

        return m44


# ============================================================================
def get_matrix44_identity(logger=None):

        return [
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ]


# ============================================================================
def array_to_matrix44(list_array, logger=None):

    list_mtx44 = []

    for n in range(len(list_array) // 16):

        pos_st = n * 16
        pos_en = n * 16 + 16
        m44 = list_array[pos_st:pos_en]

        list_mtx44.append(m44)

    return list_mtx44


# ============================================================================
def get_source_array(collada_scene, xml_node_source, logger=None):

    for xml_node in iter_xml_element_node(xml_node_source):
        if xml_node.tagName in ("IDREF_array", "Name_array"):
            return [v for v in xml_node.childNodes[0].data.split()]
        if xml_node.tagName == "float_array":
            return [float(v) for v in xml_node.childNodes[0].data.split()]
        else:
            logger.error("[get_source_array] Undefined type '%s'", xml_node.tagName)


# ============================================================================
def get_source_array_ref(collada_scene, ref_source_name, logger=None):
    """get array from xml-attribute 'source'
    """

    xml_node = collada_scene.dict_id[ref_source_name[1:]]

    if xml_node.tagName == "source":
        return get_source_array(collada_scene, xml_node, logger)
    elif xml_node.tagName == "vertices":
        xml_node_input = xml_node.getElementsByTagName("input")[0]
        return get_source_array_ref(
            collada_scene,
            xml_node_input.getAttribute("source"),
            logger
        )


# ============================================================================
def get_armature_recursive(
    collada_scene,
    xml_node,
    joint_idx, joint_idx_parent,
    list_id, list_armature, logger=None
    ):

    if xml_node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
        if xml_node.tagName == "node":
            attr_id = xml_node.getAttribute("id")
            attr_name = xml_node.getAttribute("name")
            attr_type = xml_node.getAttribute("type")

            if attr_type == "JOINT" and attr_id in list_id:
                joint_idx = len(list_armature)
                o_joint = co_type.CNodeJoint()
                o_joint.joint_idx = joint_idx
                o_joint.joint_idx_parent = joint_idx_parent
                o_joint.attr_id = attr_id
                o_joint.attr_name = attr_name
                o_joint.attr_type = attr_type
                o_joint.mtx44 = get_matrix44(xml_node.getElementsByTagName("matrix")[0])

                logger.debug(
                    "[get_armature_recursive] id = %s(%d:%d), name = %s",
                    o_joint.attr_id,
                    o_joint.joint_idx,
                    o_joint.joint_idx_parent,
                    o_joint.attr_name
                )

                list_armature.append(o_joint)

    for xml_node_child in xml_node.childNodes:
        get_armature_recursive(
            collada_scene,
            xml_node_child,
            joint_idx, joint_idx,
            list_id, list_armature, logger
        )

    return len(list_armature)


# ============================================================================
def get_armature_list(collada_scene, list_id, logger=None):

    xml_node_library = collada_scene.xml_dom.getElementsByTagName("library_visual_scenes")[0]

    for xml_node_visual_scene in xml_node_library.getElementsByTagName("visual_scene"):
        for xml_node in iter_xml_tag_name(xml_node_visual_scene, "node"):
            list_armature = []
            if get_armature_recursive(
                collada_scene,
                xml_node,
                -1, -1,
                list_id, list_armature, logger
                ) > 0:

                return list_armature

    logger.error("[get_armature_list] list_id(s) = %s", list_id)

    return None


# ============================================================================
def iter_xml_tag_name(xml_node, name):

    if isinstance(name, str) is True:
        list_name = (name,)
    else:
        list_name = name

    for xml_node_child in xml_node.childNodes:
        if xml_node_child.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
            continue
        elif xml_node_child.tagName in list_name:
            yield xml_node_child


# ============================================================================
def iter_xml_element_node(xml_node):

    for xml_node_child in xml_node.childNodes:
        if xml_node_child.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
            continue
        else:
            yield xml_node_child


# [EOF]
