"""
SBOM Dependency Graph Tool
===========================
Supports CycloneDX 1.4 and 1.6 format.

DESIGN:
  - Load SBOM file ONCE via SBOMGraph class
  - All methods reuse the same parsed data
  - No repeated file reading

Usage:
  graph = SBOMGraph("your_sbom.json")             # load once
  graph.getAllDirectDependenceNodes()              # method 1
  graph.getSubTreeByDirectNode(name, ver, group)  # method 2
"""

import json


# =============================================================================
# SBOM GRAPH CLASS — Load once, reuse everywhere
# =============================================================================

class SBOMGraph:

    def __init__(self, filepath):
        """
        Load and parse CycloneDX SBOM file ONCE.
        Build all internal maps for reuse by all methods.

        Args:
            filepath (str): path to CycloneDX SBOM file (1.4 or 1.6)
        """
        print(f"Loading SBOM file: {filepath}")

        # Load file ONCE
        with open(filepath, "r") as f:
            sbom = json.load(f)

        # Build internal maps (shared by all methods)
        self._component_map  = self._build_component_map(sbom)
        self._dependency_map = self._build_dependency_map(sbom)
        self._root_ref       = self._get_root_ref(sbom)

        print(f"Loaded successfully!")
        print(f"  Total components : {len(self._component_map)}")
        print(f"  Root component   : {self._component_map.get(self._root_ref, {}).get('name')}")


    # -------------------------------------------------------------------------
    # INTERNAL — Build maps from raw SBOM
    # -------------------------------------------------------------------------

    def _get_root_ref(self, sbom):
        """Get bom-ref of root component from metadata."""
        return sbom.get("metadata", {}).get("component", {}).get("bom-ref")


    def _build_component_map(self, sbom):
        """
        Build map: bom-ref -> { name, version, group }
        Includes root + all components.
        """
        component_map = {}

        # Root component from metadata
        root = sbom.get("metadata", {}).get("component", {})
        if root and root.get("bom-ref"):
            component_map[root["bom-ref"]] = {
                "bom_ref": root["bom-ref"],
                "name"   : root.get("name"),
                "version": root.get("version"),
                "group"  : root.get("group")
            }

        # All components
        for comp in sbom.get("components", []):
            ref = comp.get("bom-ref")
            if ref:
                component_map[ref] = {
                    "bom_ref": ref,
                    "name"   : comp.get("name"),
                    "version": comp.get("version"),
                    "group"  : comp.get("group")
                }

        return component_map


    def _build_dependency_map(self, sbom):
        """
        Build map: bom-ref -> list of children bom-refs.
        Parsed from CycloneDX 'dependencies' section.
        """
        dependency_map = {}

        for dep in sbom.get("dependencies", []):
            ref = dep.get("ref")
            if ref:
                dependency_map[ref] = dep.get("dependsOn", [])

        return dependency_map


    def _find_component_ref(self, name, version, group):
        """
        Find bom-ref of a component by name + version + group.

        Matching rules:
          - name    : exact match
          - version : exact match
          - group   : exact match (None == None is valid)
        """
        for ref, comp in self._component_map.items():
            if (comp.get("name")    == name and
                comp.get("version") == version and
                comp.get("group")   == group):
                return ref
        return None


    # -------------------------------------------------------------------------
    # METHOD 1 — getAllDirectDependenceNodes
    # -------------------------------------------------------------------------

    def getAllDirectDependenceNodes(self):
        """
        Return all direct dependency nodes of the root component.

        Direct nodes = immediate children of ROOT
                       (dependsOn list of root in dependencies section)

        Returns:
            list of dict: [ { "name": ..., "version": ..., "group": ... } ]
        """
        if not self._root_ref:
            raise ValueError("Cannot find root component in SBOM")

        # Get direct dependency refs from root
        direct_refs = self._dependency_map.get(self._root_ref, [])

        # Map refs to component info
        direct_nodes = []
        for ref in direct_refs:
            comp = self._component_map.get(ref)
            if comp:
                direct_nodes.append({
                    "name"   : comp["name"],
                    "version": comp["version"],
                    "group"  : comp["group"]
                })

        return direct_nodes


    # -------------------------------------------------------------------------
    # METHOD 2 — getSubTreeByDirectNode
    # -------------------------------------------------------------------------

    def getSubTreeByDirectNode(self, name, version, group):
        """
        Return full subtree JSON rooted at specified component.

        Subtree structure:
        {
          "name"    : "...",
          "version" : "...",
          "group"   : "...",
          "children": [ ... ]
        }

        Args:
            name    (str): component name
            version (str): component version
            group   (str): component group (can be None)

        Returns:
            dict : subtree JSON
            None : if component not found
        """

        # Find bom-ref of specified component
        target_ref = self._find_component_ref(name, version, group)

        if not target_ref:
            print(f"❌ Component not found: name='{name}' version='{version}' group='{group}'")
            return None

        # Build subtree recursively
        def build_subtree(ref, visited=None):
            if visited is None:
                visited = set()

            # Avoid infinite loop (diamond dependencies)
            if ref in visited:
                return None

            visited.add(ref)

            comp = self._component_map.get(ref)
            if not comp:
                return None

            node = {
                "name"    : comp["name"],
                "version" : comp["version"],
                "group"   : comp["group"],
                "children": []
            }

            for child_ref in self._dependency_map.get(ref, []):
                child_node = build_subtree(child_ref, visited)
                if child_node is not None:
                    node["children"].append(child_node)

            return node

        return build_subtree(target_ref)


# =============================================================================
# MAIN — RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":

    FILEPATH = "sample_sbom.json"

    # -------------------------------------------------------------------------
    # Load SBOM file ONCE — reused by all methods below
    # -------------------------------------------------------------------------
    print("=" * 60)
    graph = SBOMGraph(FILEPATH)

    # -------------------------------------------------------------------------
    # METHOD 1: getAllDirectDependenceNodes
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("METHOD 1: getAllDirectDependenceNodes()")
    print("=" * 60)

    direct_nodes = graph.getAllDirectDependenceNodes()

    print(f"\nTotal direct dependencies: {len(direct_nodes)}")
    print("\nResult:")
    for i, node in enumerate(direct_nodes, 1):
        print(f"  [{i}] name={node['name']}, version={node['version']}, group={node['group']}")

    print(f"\nRaw output:")
    print(json.dumps(direct_nodes, indent=2))

    # -------------------------------------------------------------------------
    # METHOD 2: getSubTreeByDirectNode
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("METHOD 2: getSubTreeByDirectNode()")
    print("=" * 60)

    # Test 1 — @typespec/ts-http-runtime (large subtree)
    print("\nTest 1 — ts-http-runtime@0.3.2 (group=@typespec)")
    print("-" * 60)
    subtree = graph.getSubTreeByDirectNode("ts-http-runtime", "0.3.2", "@typespec")
    if subtree:
        group = f"{subtree['group']}/" if subtree['group'] else ""
        print(f"Subtree root    : {group}{subtree['name']}@{subtree['version']}")
        print(f"Direct children : {len(subtree['children'])}")
        print(f"\nSubtree JSON:")
        print(json.dumps(subtree, indent=2))

    # Test 2 — tslib (leaf node)
    print("\n" + "=" * 60)
    print("Test 2 — tslib@2.8.1 (leaf node, group=None)")
    print("-" * 60)
    subtree2 = graph.getSubTreeByDirectNode("tslib", "2.8.1", None)
    if subtree2:
        print(f"Subtree root    : {subtree2['name']}@{subtree2['version']}")
        print(f"Direct children : {len(subtree2['children'])}")
        print(json.dumps(subtree2, indent=2))

    # Test 3 — Not found
    print("\n" + "=" * 60)
    print("Test 3 — Component not found")
    print("-" * 60)
    subtree3 = graph.getSubTreeByDirectNode("unknown-lib", "9.9.9", None)
    print(f"Result: {subtree3}")
