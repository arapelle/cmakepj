import re


class CLCommand:
    def __init__(self, arg_name=None):
        self.__subcommand_label = arg_name if arg_name else self.default_subcommand_label()

    def subcommand_label(self):
        return self.__subcommand_label

    def default_subcommand_label(self):
        return f"{self.class_name_label()}-subcommand"

    def class_name_label(self):
        name_comps = re.findall('[A-Z][^A-Z]*', self.__class__.__name__)
        return '-'.join([x.lower() for x in name_comps])

    def invoke(self, args):
        arg_name = getattr(args, self.subcommand_label())
        arg_name = arg_name.replace('-', '_')
        if hasattr(self.__class__, arg_name):
            method = getattr(self.__class__, arg_name)
            delattr(args, self.subcommand_label())
            method(self, args)
        elif hasattr(self, arg_name):
            field = getattr(self, arg_name)
            delattr(args, self.subcommand_label())
            field.invoke(args)
        else:
            print(f"error: Missing field or method '{arg_name}' in class {self.__class__.__name__}.")
            exit(-1)
