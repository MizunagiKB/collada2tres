# -*- coding: utf-8 -*-


class CColladaGeometory:

    def __init__(self):
        self.geometry_name = ""

        # for Godot
        self.material = None
        self.material_index = None
        self.material_name = None

        self.mesh_virt_size = 0
        self.varray_virt = None
        self.varray_norm = None
        self.varray_tex1 = []
        self.varray_tex2 = []
        self.skin_virt_size = 0
        self.varray_j = []
        self.varray_w = []


class CColladaItem:

    def __init__(self):
        self.up_axis = None

        self.dict_source_controllers = {}
        self.dict_source_morph = {}
        self.morph_targets_map = None

        self.dict_source_mesh = {}

        self.dict_armature = None
        self.dict_material = None

        self.skin_j = None
        self.skin_w = None

        self.list_geometry = []

        self.list_morph_name = []
        self.dict_morph = {}


class COffsetMap:

    def __init__(self):
        self.list_input = []

    def set(self, semantic, source, offset):
        self.list_input.append(
            {
                "semantic": semantic,
                "source": source,
                "offset": offset
            }
        )

    def get_stride_size(self):
        n_max = 0

        for dict_item in self.list_input:
            if dict_item["offset"] > n_max:
                n_max = dict_item["offset"]

        return n_max + 1

    def get_source(self, semantic):

        for dict_item in self.list_input:
            if dict_item["semantic"] == semantic:
                return dict_item["source"]

    def get_offset(self, semantic):

        for dict_item in self.list_input:
            if dict_item["semantic"] == semantic:
                return dict_item["offset"]


def create_offset_map(o_node, name):

    offset_map = COffsetMap()

    for o_node_sub in o_node.getElementsByTagName(name):
        attr_semantic = o_node_sub.getAttribute("semantic")
        attr_source = o_node_sub.getAttribute("source")[1:]
        try:
            attr_offset = int(o_node_sub.getAttribute("offset"))
        except:
            attr_offset = 0

        offset_map.set(
            attr_semantic,
            attr_source,
            attr_offset
        )

    return offset_map


def array_loader(o_node, name, o_logger):

    o_node_sub = o_node.getElementsByTagName(name)[0]
    for v in o_node_sub.childNodes:
        if v.nodeType == o_node.TEXT_NODE:
            if name in ("IDREF_array", "Name_array"):
                return [v for v in v.data.split()]
            elif name in ("vcount","v", "p"):
                return [int(v) for v in v.data.split()]
            elif name in ("float_array",):
                return [float(v) for v in v.data.split()]

    o_logger.error("convert error, %s", name)

    return None
