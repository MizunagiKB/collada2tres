# -*- coding: utf-8 -*-
# ------------------------------------------------------------------ import(s)
import sys

import collada.collada_type as co_type


# ------------------------------------------------------------------- param(s)
# ------------------------------------------------------------------- class(s)
# ---------------------------------------------------------------- function(s)
# ============================================================================
def load_library_materials(collada_scene, xml_node_library, logger=None):

    resource_ridx = 1

    for xml_node in xml_node_library.getElementsByTagName("material"):
        attr_id = xml_node.getAttribute("id")
        attr_name = xml_node.getAttribute("name")

        o_material = co_type.CMaterial()
        o_material.attr_id = attr_id
        o_material.attr_name = attr_name

        if collada_scene.o_argv.MATERIAL is None:
            o_material.resource_ridx = resource_ridx
            collada_scene.dict_material[attr_id] = o_material

            logger.debug("material> id = %s, name = %s (resource_idx = %d)", attr_id, attr_name, resource_ridx)

            resource_ridx += 1

        elif o_material.attr_id in collada_scene.o_argv.MATERIAL:
            o_material.resource_ridx = resource_ridx
            collada_scene.dict_material[attr_id] = o_material

            logger.debug("material> id = %s, name = %s (resource_idx = %d)", attr_id, attr_name, resource_ridx)

            resource_ridx += 1

    return True



# [EOF]
