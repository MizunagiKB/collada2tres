# -*- coding: utf-8 -*-
# ------------------------------------------------------------------ import(s)
import sys
#import collada_lib


# ------------------------------------------------------------------- param(s)
# ------------------------------------------------------------------- class(s)
# ----------------------------------------------------------------------------
class CInput:
    def __init__(self):
        self.attr_semantic = None
        self.attr_offset = None
        self.attr_set = None

        self.src = []
        self.dst = []


# ----------------------------------------------------------------------------
class CMesh:
    def __init__(self):
        self.attr_geometry_id = ""
        self.attr_geometry_name = ""

        self.attr_material = ""

        self.material_ridx = ""
        self.material_name = ""

        self.dict_input = {}
        self.max_offset = 0
        self.list_vcount = []
        self.list_p = []

        self.with_armature = False
        self.with_morph = False

        self.mesh_virt_size = 0


# ----------------------------------------------------------------------------
class CGeometry:
    """
        list_mesh []
    """

    def __init__(self, collada_scene):
        #
        self.collada_scene = collada_scene

        self.attr_geometry_id = None
        self.attr_geometry_name = None

        self.list_mesh = []
        self.o_morph = None

        # for Godot
#        self.material = None
#        self.material_index = None
#        self.material_name = None

        self.varray_virt = None
        self.varray_norm = None
        self.varray_tex1 = []
        self.varray_tex2 = []
        self.skin_virt_size = 0
        self.varray_j = []
        self.varray_w = []


# ----------------------------------------------------------------------------
class CMaterial:
    def __init__(self):
        self.resource_ridx = None
        self.attr_id = None
        self.attr_name = None


# ----------------------------------------------------------------------------
class CController:
    __slots__ = [
        "attr_controller_id",
        "attr_controller_name",
        "o_skin",
        "o_morph"
    ]
    def __init__(self):
        self.attr_controller_id = None
        self.attr_controller_name = None

        self.o_skin = None
        self.o_morph = None

# ----------------------------------------------------------------------------
class CMorph:
    def __init__(self):
        self.method = ""
        self.dict_input = {}

# ----------------------------------------------------------------------------
class CNodeJoint:
    __slots__ = [
        "joint_idx",
        "joint_idx_parent",
        "attr_id",
        "attr_name",
        "attr_type",
        "mtx44"
    ]
    def __init__(self):
        self.joint_idx = None
        self.joint_idx_parent = None
        self.attr_id = None
        self.attr_name = None
        self.attr_type = None
        self.mtx44 = None


# ----------------------------------------------------------------------------
class CSkin:
    def __init__(self):
        self.attr_source = None

        self.dict_input = {}
        self.max_offset = 0
        self.list_vcount = []
        self.list_v = []

        self.list_mtx44 = []

        self.o_geometry = None


# ----------------------------------------------------------------------------
class CNode:
    __slots__ = [
        "collada_scene",

        "xml_node_matrix",
        "mtx44",

        "xml_node_instance",
        "instance_type",

        "attr_instance_url",
        "attr_instance_name",
        "o_instance"
    ]
    def __init__(self, collada_scene):
        #
        self.collada_scene = collada_scene
        self.xml_node_matrix = None
        self.mtx44 = None

        self.xml_node_instance = None
        self.instance_type = None

        self.attr_instance_url = None
        self.attr_instance_name = None

        self.o_instance = None


# ----------------------------------------------------------------------------
class CColladaScene:

    def __init__(self):
        self.o_argv = None
        self.xml_dom = None

        self.unit_name = None
        self.unit_value = None
        self.up_axis = None

        self.dict_id = {}
        self.dict_ref_source = {}

        # node
        self.list_node = []
        self.list_skin = []


        # library_geometries
        self.dict_geometry = {}

        # library_controllers
        self.dict_morph = {}

        # library_materials
        self.dict_material = {}
        self.bind_material = {}

        # library_materials
        self.dict_controller = {}


# ---------------------------------------------------------------- function(s)



# [EOF]
