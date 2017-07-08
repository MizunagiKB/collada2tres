# -*- coding: utf-8 -*-
# ------------------------------------------------------------------ import(s)
import sys
import xml.dom.minidom
import logging
import argparse

import collada.collada_type as co_type
import collada.collada_util as co_util

import collada.lib_material as lib_material
import collada.lib_geometry as lib_geometry
import collada.lib_controller as lib_controller

import export.export_godot as exp_godot


# ------------------------------------------------------------------- param(s)
LOGGING_FORMAT = "%(asctime)-15s %(levelname)8s %(message)s"


# ---------------------------------------------------------------- function(s)
# ============================================================================
def load_node_instance(collada_scene, o_node, instance_type, url, logger=None):

    if instance_type not in ["instance_camera", "instance_controller", "instance_geometry", "instance_light"]:
        logger.error("not support instance type '%s'", instance_type)

    elif instance_type == "instance_camera":
        pass

    elif instance_type == "instance_controller":

        xml_node_controller = collada_scene.dict_id[url[1:]]

        o_node.o_instance = lib_controller.create_controller(
            collada_scene,
            xml_node_controller,
            logger
        )

        return True

    elif instance_type == "instance_geometry":

        xml_node_geometry = collada_scene.dict_id[url[1:]]

        o_node.o_instance = lib_geometry.create_geometry(
            collada_scene,
            xml_node_geometry,
            logger
        )

        return True

    elif instance_type == "instance_light":
        pass

    return False


# ============================================================================
def load_visual_scene(o_argv, xml_dom, attr_url, collada_scene, logger=None):

    xml_node_scene = collada_scene.dict_id[attr_url[1:]]

    for xml_node in co_util.iter_xml_tag_name(
        xml_node_scene,
        "node"
        ):

        attr_id = xml_node.getAttribute("id")
        attr_name = xml_node.getAttribute("name")
        attr_type = xml_node.getAttribute("type")

        logger.debug("visual_scene>node> id = %s, name = %s, type = %s", attr_id, attr_name, attr_type)

        o_node = co_type.CNode(collada_scene)
        for xml_node_matrix in co_util.iter_xml_tag_name(xml_node, "matrix"):
            o_node.xml_node_matrix = xml_node_matrix
            o_node.mtx44 = co_util.get_matrix44(xml_node_matrix)

        if o_node.xml_node_matrix is None:
            o_node.xml_node_matrix = None
            o_node.mtx44 = co_util.get_matrix44_identity()
            logger.warn("[load_visual_scene] '<matrix>' node not found.")

        for xml_node_instance in co_util.iter_xml_tag_name(
            xml_node, ["instance_camera", "instance_controller", "instance_geometry", "instance_light"]
            ):

            o_node.xml_node_instance = xml_node_instance
            o_node.instance_type = xml_node_instance.tagName

            o_node.attr_instance_url = xml_node_instance.getAttribute("url")
            o_node.attr_instance_name = xml_node_instance.getAttribute("name")

            if load_node_instance(
                collada_scene,
                o_node,
                o_node.instance_type,
                o_node.attr_instance_url,
                logger
                ) is True:

                collada_scene.list_node.append(o_node)


# ============================================================================
def search_xml_node_id(xml_dom, xml_node, collada_item, logger=None):

    for xml_node_child in xml_node.childNodes:
        if xml_node_child.nodeType == xml_dom.ELEMENT_NODE:
            attr_id = xml_node_child.getAttribute("id")

            if len(attr_id) > 0:
                if attr_id in collada_item.dict_id:
                    logger.critical("id '%s' is not unique.", attr_id)
                    sys.exit(-1)

                collada_item.dict_id[attr_id] = xml_node_child

            search_xml_node_id(
                xml_dom,
                xml_node_child,
                collada_item
            )

# ============================================================================
def search_xml_node_ref_source(xml_dom, xml_node, collada_item, logger=None):

    for xml_node_child in xml_node.childNodes:
        if xml_node_child.nodeType == xml_dom.ELEMENT_NODE:
            attr_source = xml_node_child.getAttribute("source")

            if len(attr_source) > 0:
                if attr_source not in collada_item.dict_ref_source:
                    collada_item.dict_ref_source[attr_source] = []
                collada_item.dict_ref_source[attr_source].append(xml_node)

            search_xml_node_ref_source(
                xml_dom,
                xml_node_child,
                collada_item
            )


# ============================================================================
def parse(o_argv, xml_dom, logger=None):

    collada_scene = co_type.CColladaScene()
    collada_scene.o_argv = o_argv
    collada_scene.xml_dom = xml_dom

    # Check UP Axis
    o_node = xml_dom.getElementsByTagName("asset")[0].getElementsByTagName("up_axis")[0]
    up_axis = o_node.childNodes[0].data.strip().upper()
    collada_scene.up_axis = up_axis
    logger.info("asset>up_axis> %s", up_axis)

    # Check Unit
    o_node = xml_dom.getElementsByTagName("asset")[0].getElementsByTagName("unit")[0]
    unit_name = o_node.getAttribute("name")
    unit_value = float(o_node.getAttribute(unit_name))
    collada_scene.unit_name = unit_name
    collada_scene.unit_value = unit_value
    logger.info("asset>unit> name = %s, value = %f", unit_name, unit_value)

    search_xml_node_id(xml_dom, xml_dom, collada_scene, logger)
    logger.info("found id count %d", len(collada_scene.dict_id))

    search_xml_node_ref_source(xml_dom, xml_dom, collada_scene, logger)
    logger.info("found ref source count %d", len(collada_scene.dict_ref_source))

    #
    for xml_node in xml_dom.getElementsByTagName("library_materials"):
        lib_material.load_library_materials(
            collada_scene, xml_node, logger
        )

    #
#    for xml_node in xml_dom.getElementsByTagName("library_controllers"):
#        lib_controller.load_library_controllers(
#            collada_scene, xml_node, logger
#        )

    # decode scene
    xml_node_scene = xml_dom.getElementsByTagName("scene")[0]

    for xml_node_instance in co_util.iter_xml_tag_name(
        xml_node_scene,
        "instance_visual_scene"
        ):

        attr_url = xml_node_instance.getAttribute("url")

        load_visual_scene(o_argv, xml_dom, attr_url, collada_scene, logger)

    return collada_scene


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
    o_parser.add_argument(
        "--wo-morph",
        action="store_true",
        dest="WO_MORPH",
        default=False,
        help="Without Mesh morph"
    )
    o_parser.add_argument(
        "--wo-skin",
        action="store_true",
        dest="WO_SKIN",
        default=False,
        help="Without Mesh skin"
    )

    o_argv = o_parser.parse_args()

    if o_argv.MATERIAL is not None:
        o_argv.MATERIAL = [name.strip() for name in o_argv.MATERIAL.split(",")]

    logging.basicConfig(format=LOGGING_FORMAT)

    o_logger = logging.getLogger(__name__)
    if o_argv.VERBOSE is False:
        o_logger.setLevel(logging.ERROR)
    else:
        o_logger.setLevel(logging.DEBUG)

    o_dom = xml.dom.minidom.parse(o_argv.I_FILE)

    if o_dom.documentElement.tagName.strip() != "COLLADA":
        o_log.error("File type error.")

    collada_scene = parse(o_argv, o_dom, o_logger)

    exp_godot.export(collada_scene)


if __name__ == "__main__":
    main()



# [EOF]
