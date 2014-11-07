import operator as op
import ast
import re
from decimal import Decimal
from analysis.abstract import Dimension, Property, DatabaseSource, DataView
from analysis.core.models import FieldType


operators = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor
}


def eval_ast(node, values=None):
    if isinstance(node, ast.Num):
        # <number>
        return node.n

    elif isinstance(node, ast.operator):
        # <operator>
        return operators[type(node)]

    elif isinstance(node, ast.BinOp):
        # <left> <operator> <right>
        return eval_ast(node.op, values)(
            eval_ast(node.left, values),
            eval_ast(node.right, values)
        )

    elif values and node.id in values:
        return values[node.id]

    else:
        raise TypeError(node)


def parse_expression(expr, values=None):
    """
    >>> parse_expression('2^6')
    4
    >>> parse_expression('2**6')
    64
    >>> parse_expression('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    # Module(body=[Expr(value=...)])
    return eval_ast(
        ast.parse(expr).body[0].value,
        values)


def build_parser_closure(expression, sources):
    def clean(*values):
        assert len(sources) == len(values)
        values = [Decimal(str(v)) for v in values]
        result = parse_expression(expression, dict(zip(sources, values)))
        if result == 0:
            return int(0)
        return float('%.3f' % result)

    return clean

def build_parser_closure_for_percent(expression, sources):
    def clean(*values):
        assert len(sources) == len(values)
        values = [Decimal(str(v)) for v in values]
        result = parse_expression(expression, dict(zip(sources, values)))
        return float('%.6f' % result)

    return clean

def build_data_view(report):
    fields = report.fields.all()
    dims = []
    props = []
    regex = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)')
    for field in fields:
        if field.type == FieldType.DIMENSION:
            dims.append(Dimension(field.display, field.data_type, field.source))

        else:
            if field.expression:
                sources = regex.findall(field.expression)
                if field.data_type == 'number':
                    clean_method = build_parser_closure(field.expression, sources)
                elif field.data_type == 'percent':
                    clean_method = build_parser_closure_for_percent(field.expression, sources)
                else:
                    clean_method = None
            else:
                sources = [field.source]
                clean_method = None
            props.append(Property(field.display, field.data_type, sources, clean=clean_method))

    data_source = DatabaseSource(report.database.stringify(), report.table)
    view = DataView(report.name, dims, props, data_source)
    return view
