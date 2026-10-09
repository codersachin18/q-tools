"""BaseTool framework and registry."""

import importlib
import pkgutil


class BaseTool:
    """Base class every tool inherits from.

    Subclasses set `id`, `name`, `category`, `icon`, `description`.
    Override `build(self, parent)` to create the UI inside the given frame.
    """

    id: str = ""
    name: str = ""
    category: str = ""
    icon: str = "🧰"
    description: str = ""
    keywords: list = []

    def __init__(self, app=None):
        self.app = app

    def build(self, parent):
        raise NotImplementedError

    def get_meta(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "icon": self.icon,
            "description": self.description,
            "keywords": self.keywords,
        }


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool_cls):
        inst = tool_cls()
        if not inst.id or not inst.name:
            return  # abstract/base class
        self._tools[inst.id] = inst

    def get(self, tid):
        return self._tools.get(tid)

    def all(self):
        return list(self._tools.values())

    def by_category(self, cat):
        return [t for t in self._tools.values() if t.category == cat]

    def categories(self):
        cats = []
        for t in self._tools.values():
            if t.category not in cats:
                cats.append(t.category)
        return cats

    def search(self, query):
        q = query.strip().lower()
        if not q:
            return list(self._tools.values())
        results = []
        for t in self._tools.values():
            hay = (f"{t.name} {t.description} {' '.join(t.keywords)} {t.category}").lower()
            score = 0
            if t.name.lower() == q:
                score += 100
            elif t.name.lower().startswith(q):
                score += 60
            elif q in hay:
                score += 30
            if score:
                results.append((score, t))
        results.sort(key=lambda x: -x[0])
        return [t for _, t in results]


def discover_tools():
    """Auto-discover all tool modules under tools/ package."""
    registry = ToolRegistry()
    import tools as tools_pkg
    for _, modname, _ in pkgutil.iter_modules(tools_pkg.__path__):
        if modname.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"tools.{modname}")
        except Exception as e:
            print(f"Failed to import tool module {modname}: {e}")
            continue
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, BaseTool) and obj is not BaseTool:
                # only register concrete classes defined in this module
                if obj.__module__ == mod.__name__ and obj.id and obj.name:
                    try:
                        registry.register(obj)
                    except Exception as e:
                        print(f"Failed to register {obj}: {e}")
    return registry


# Categories shown in the sidebar
CATEGORIES = [
    ("all", "All Tools"),
    ("file", "File & System"),
    ("text", "Text & Codec"),
    ("image", "Image"),
    ("converter", "Converter"),
    ("system", "System"),
    ("misc", "Misc"),
]