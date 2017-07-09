# -*- coding: utf-8 -*-
import jinja2
# ------------------------------------------------------------------ import(s)
import collada.collada_util as co_util


# ------------------------------------------------------------------- param(s)
ENCODE = "utf-8"


# ------------------------------------------------------------------- class(s)
# ---------------------------------------------------------------- function(s)
# ============================================================================
def vertex_length(list_vertex, vertex_count):
    return len(list_vertex) // vertex_count


# ============================================================================
def skinning_vertex(o_skin, input_type, o_mesh):

    list_result = []

    n_pos = 0
    stride_size = o_mesh.max_offset + 1

    for v_count in o_mesh.list_vcount:

        for n in range(v_count):
            list_data = o_mesh.list_p[n_pos:n_pos + stride_size]

            o_input = o_mesh.dict_input["VERTEX_0"]

            ref_addr = list_data[o_input.attr_offset]

            if input_type == "JOINT_0":
                for o_joint in o_skin.dict_input[input_type].dst[ref_addr]:
                    if isinstance(o_joint, int) is True:
                        list_result.append(o_joint)
                    else:
                        list_result.append(o_joint.joint_idx)
            elif input_type == "WEIGHT_0":
                list_result += o_skin.dict_input[input_type].dst[ref_addr]

            n_pos += stride_size

    return list_result


# ============================================================================
def render_node(jinja2_env, collada_scene, render_data, resource_idx):

    render_data += jinja2.Template(
"""
[node name="scene_root" type="Spatial"]

_import_path = NodePath(".")
_import_transform = Transform( 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 )

"""
    ).render()

    resource_count = 0
    for o_node in collada_scene.list_node:

        if o_node.instance_type in ("instance_controller", "instance_geometry"):

            if o_node.instance_type == "instance_controller":
                o_geometry = o_node.o_instance.o_skin.o_geometry
                o_morph = o_geometry.o_morph
                o_skin = o_node.o_instance.o_skin
            elif o_node.instance_type == "instance_geometry":
                o_geometry = o_node.o_instance
                o_morph = o_geometry.o_morph
                o_skin = None

            if len(o_geometry.list_mesh) > 0:

                if collada_scene.o_argv.WO_MORPH is True:
                    o_morph = None

                if collada_scene.o_argv.WO_SKIN is True:
                    o_skin = None

                render_data += jinja2_env.from_string(
"""
[node name="{{ o_geometry.attr_geometry_name }}" type="Spatial" parent="."]

_import_path = NodePath("{{ o_geometry.attr_geometry_name }}")
_import_transform = Transform( 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 )

{% if o_skin -%}
[node name="Skeleton" type="Skeleton" parent="{{ o_geometry.attr_geometry_name }}"]

_import_path = NodePath("{{ o_geometry.attr_geometry_name }}/Skeleton")
_import_transform = Transform( 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 )
{% for idx in range(o_skin.dict_input["JOINT_0"].src|length) -%}
{% for o_node_joint in o_skin.dict_input["JOINT_0"].src -%}
{% if o_node_joint.joint_idx == idx -%}
bones/{{ o_node_joint.joint_idx }}/name = "{{ o_node_joint.attr_name }}"
bones/{{ o_node_joint.joint_idx }}/parent = {{ o_node_joint.joint_idx_parent }}
{# bones/{{ o_node_joint.joint_idx }}/rest = Transform( {% for v in o_node_joint.mtx34 %}{{ v }}{% if loop.last == false %}, {% endif %}{% endfor %} ) #}
bones/{{ o_node_joint.joint_idx }}/rest = Transform( {% for v in o_node_joint.mtx44|convert_mtx44_to_mtx34 %}{{ v }}{% if loop.last == false %}, {% endif %}{% endfor %} )
bones/{{ o_node_joint.joint_idx }}/enabled = true
bones/{{ o_node_joint.joint_idx }}/bound_childs = []
{% endif -%}
{% endfor -%}
{% endfor %}
{% endif -%}
[node name="Mesh" type="MeshInstance" parent="{{ o_geometry.attr_geometry_name }}{% if o_skin %}/Skeleton{% endif %}"]

_import_path = NodePath("{{ o_geometry.attr_geometry_name }}{% if o_skin %}/Skeleton{% endif %}/Mesh")
_import_transform = Transform( 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 )
layers = 1
geometry/visible = true
geometry/material_override = null
geometry/cast_shadow = 1
geometry/receive_shadows = true
geometry/range_begin = 0.0
geometry/range_end = 0.0
geometry/extra_cull_margin = 0.0
geometry/billboard = false
geometry/billboard_y = false
geometry/depth_scale = false
geometry/visible_in_all_rooms = false
geometry/use_baked_light = true
geometry/baked_light_tex_id = 0
mesh/mesh = SubResource( {{ resource_idx }} )
mesh/skeleton = NodePath("..")
{% for o_mesh in o_geometry.list_mesh -%}
material/{{ loop.index0 }} = null
{% endfor -%}

"""
                ).render(
                    o_geometry=o_geometry,
                    o_skin=o_skin,
                    resource_idx=resource_idx + resource_count
                )

                resource_count += 1

    return render_data, resource_idx + resource_count


# ============================================================================
def render_mesh(jinja2_env, collada_scene, render_data, resource_idx):

    resource_count = 0
    for o_node in collada_scene.list_node:

        if o_node.instance_type in ("instance_controller", "instance_geometry"):

            if o_node.instance_type == "instance_controller":
                o_geometry = o_node.o_instance.o_skin.o_geometry
                o_morph = o_geometry.o_morph
                o_skin = o_node.o_instance.o_skin
            elif o_node.instance_type == "instance_geometry":
                o_geometry = o_node.o_instance
                o_morph = o_geometry.o_morph
                o_skin = None

            if len(o_geometry.list_mesh) > 0:

                if collada_scene.o_argv.WO_MORPH is True:
                    o_morph = None

                if collada_scene.o_argv.WO_SKIN is True:
                    o_skin = None

                render_data += jinja2_env.from_string(
"""
[sub_resource type="Mesh" id={{ resource_idx }}]

resource/name = "{{ o_geometry.attr_geometry_name }}"
{% if o_morph -%}
morph_target/mode = 0
morph_target/names = [
    {% for o_geometry_morph in o_morph.dict_input["MORPH_TARGET_0"].dst -%}
        "{{ o_geometry_morph.attr_geometry_name }}"{% if loop.last == false -%}, {% endif -%}
    {% endfor -%}
]
{% endif -%}
{% for o_mesh in o_geometry.list_mesh -%}
surfaces/{{ loop.index0 }} = {
"name": "{{ o_mesh.material_name }}",
"material": SubResource( {{ o_mesh.material_ridx }} ),
"primitive": 4,
"alphasort": false,
"arrays": [
Vector3Array(
{% for v in o_mesh.dict_input["VERTEX_0"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
Vector3Array(
{% for v in o_mesh.dict_input["NORMAL_0"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
null, null,
{% if "TEXCOORD_0" in o_mesh.dict_input %}
Vector2Array(
{% for v in o_mesh.dict_input["TEXCOORD_0"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
{% else %}
null,
{% endif %}
{% if "TEXCOORD_1" in o_mesh.dict_input %}
Vector2Array(
{% for v in o_mesh.dict_input["TEXCOORD_1"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
{% else %}
null,
{% endif %}
{% if o_skin and o_morph == None %}
FloatArray(
{% for v in o_skin|skinning_vertex("JOINT_0", o_mesh) %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
FloatArray(
{% for v in o_skin|skinning_vertex("WEIGHT_0", o_mesh) %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
{% else %}
null,
null,
{% endif %}
IntArray(
{% for v in range(o_mesh.dict_input["VERTEX_0"].dst|vertex_length(3)) %}{{ v }}{% if loop.last == false %}, {% endif %}{% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endfor %}
)
],
"morph_arrays": [
{% if o_morph -%}
{% for o_geometry_morph in o_morph.dict_input["MORPH_TARGET_0"].dst -%}
{% set morph_loop = loop %}
{% for o_mesh_morph in o_geometry_morph.list_mesh -%}
{% if o_mesh_morph.attr_material == o_mesh.attr_material -%}
[
Vector3Array(
{% for v in o_mesh_morph.dict_input["VERTEX_0"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
Vector3Array(
{% for v in o_mesh_morph.dict_input["NORMAL_0"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
null, null,
{% if "TEXCOORD_0" in o_mesh_morph.dict_input %}
Vector2Array(
{% for v in o_mesh_morph.dict_input["TEXCOORD_0"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
),
{% else %}
null,
{% endif %}
{% if "TEXCOORD_1" in o_mesh_morph.dict_input %}
Vector2Array(
{% for v in o_mesh_morph.dict_input["TEXCOORD_1"].dst %}{{ v }}{% if loop.last == false %}, {% if (loop.index % 12) == 0 %}{{ "\n" }}{% endif %}{% endif %}{% endfor %}
)
{% else %}
null
{% endif %}
]{% if morph_loop.last == false %},{% endif %}
{% endif -%}
{% endfor -%}
{% endfor -%}
{% endif -%}
]
}
{% endfor -%}
custom_aabb/custom_aabb = AABB( 0, 0, 0, 0, 0, 0 )

"""
                ).render(
                    collada_scene=collada_scene,
                    o_geometry=o_geometry,
                    o_morph=o_morph,
                    o_skin=o_skin,
                    resource_idx=resource_idx + resource_count
                )

                resource_count += 1

    return render_node(jinja2_env, collada_scene, render_data, resource_idx)


# ============================================================================
def render_material(jinja2_env, collada_scene, resource_idx):

    render_data = jinja2_env.from_string(
"""
{% for idx in range(collada_scene.dict_material|count) -%}
{% for attr_id, o_material in collada_scene.dict_material.items() -%}
{% if o_material.resource_ridx == (idx + 1) -%}
[sub_resource type="FixedMaterial" id={{ o_material.resource_ridx }}]

resource/name = "{{ o_material.attr_name }}"
flags/visible = true
flags/double_sided = false
flags/invert_faces = true
flags/unshaded = false
flags/on_top = false
flags/lightmap_on_uv2 = true
flags/colarray_is_srgb = true
params/blend_mode = 0
params/depth_draw = 1
params/line_width = 0.0
fixed_flags/use_alpha = false
fixed_flags/use_color_array = false
fixed_flags/use_point_size = false
fixed_flags/discard_alpha = false
fixed_flags/use_xy_normalmap = false
params/diffuse = Color( 0.64, 0.64, 0.64, 1 )
params/specular = Color( 0, 0, 0, 1 )
params/emission = Color( 0, 0, 0, 1 )
params/specular_exp = 0.0
params/detail_mix = 1.0
params/normal_depth = 1
params/shader = 0
params/shader_param = 0.5
params/glow = 0
params/point_size = 1.0
uv_xform = Transform( 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 )
textures/diffuse_tc = 0
textures/detail_tc = 0
textures/specular_tc = 0
textures/emission_tc = 0
textures/specular_exp_tc = 0
textures/glow_tc = 0
textures/normal_tc = 0
textures/shade_param_tc = 0
{%- endif %}
{%- endfor %}

{% endfor -%}
"""
    ).render(
        collada_scene=collada_scene,
        resource_idx=resource_idx
    )

    resource_idx += len(collada_scene.dict_material)

    return render_mesh(jinja2_env, collada_scene, render_data, resource_idx + 1)


# ============================================================================
def export(collada_scene):

    jinja2_env = jinja2.Environment()
    jinja2_env.filters["convert_mtx44_to_mtx34"] = co_util.convert_mtx44_to_mtx34
    jinja2_env.filters["vertex_length"] = vertex_length
    jinja2_env.filters["skinning_vertex"] = skinning_vertex

    render_data, resource_idx = render_material(jinja2_env, collada_scene, 0)

    export_filename = collada_scene.o_argv.O_FILE

    with open(export_filename, "wb") as h_writer:
        h_writer.write(
            "[gd_scene load_steps={:d} format=1]\n{}".format(
                resource_idx,
                render_data
            ).encode(ENCODE)
        )



# [EOF]
