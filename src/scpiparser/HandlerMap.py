
class DuplicateHandlerException(Exception):
    pass

class HandlerMapNode:
    def __init__(self,handler=None):
        self.handler = handler
        self.children = {}
    def get_children(self):
        return self.children
    def get_handler(self):
        return self.handler
    def set_handler(self,handler):
        self.handler = handler

class HandlerMap:
    def __init__(self):
        self.map = {}

    def register_handler(self,name,handler):
        name_parts = name.split(":")
        short_name_parts = self._to_short_names(name_parts)
        name_parts = list(map(lambda name: name.upper(),name_parts))
        self._add_entry(name_parts,self.map,handler)
        self._add_entry(short_name_parts,self.map,handler)

    def find_handler(self,name):
        name_parts = name.upper().split(":")
        return self._find_entry(name_parts,self.map)

    def _add_entry(self,name_parts,nodes,handler):
        name_part = name_parts[0]
        last_part = (len(name_parts) == 1)
        if name_part in nodes:
            if last_part:
                if nodes[name_part].get_handler() and nodes[name_part].get_handler() != handler:
                    raise DuplicateHandlerException
                nodes[name_part].set_handler(handler)
            else:
                self._add_entry(name_parts[1:],nodes[name_part].get_children(),handler)
        else:
            nodes[name_part] = HandlerMapNode(handler if last_part else None)
            if not last_part:
                self._add_entry(name_parts[1:],nodes[name_part].get_children(),handler)

    def _find_entry(self,name_parts,nodes):
        name_part = name_parts[0]
        last_part = (len(name_parts) == 1)
        if name_part in nodes:
            if last_part:
                return nodes[name_part].get_handler()
            else:
                return self._find_entry(name_parts[1:],nodes[name_part].get_children())
        else:
            return None

    def _to_short_names(self,name_parts):
        short_name_parts = []
        for name in name_parts:
            short_name_parts.append(self._short_name(name))
        return short_name_parts

    def _short_name(self,name):
        short_name = ""
        for next_char in name:
            if next_char.isupper() :
                short_name = short_name + next_char
            else:
                break
        return short_name
