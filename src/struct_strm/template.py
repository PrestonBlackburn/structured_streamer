from functools import lru_cache
from jinja2 import Environment, PackageLoader, Template

package_loader = PackageLoader("struct_strm", "templates")

jinja2_env = Environment(loader=package_loader, lstrip_blocks=True, trim_blocks=True)


@lru_cache(maxsize=1)
def template(template_name: str) -> Template:
    return jinja2_env.get_template(template_name)
