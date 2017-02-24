# -*- coding: utf-8 -*-

FIELDS = ['identifier', 'attribute', 'value']

OP_EQUAL = 0
OP_COMPARE = 1


class BetaNode(object):

    def __init__(self, children=None, parent=None):
        self.children = children if children else []
        self.parent = parent


class Condition:

    def __init__(self, identifier, attribute, value, positive=True):
        """
        (<x> ^self <y>)
        repr as:
        ('$x', 'self', '$y')

        :type value: Var or str
        :type attribute: Var or str
        :type identifier: Var or str
        """
        self.value = value
        self.attribute = attribute
        self.identifier = identifier
        self.positive = positive

    @property
    def vars(self):
        """
        :rtype: list
        """
        ret = []
        for field in FIELDS:
            v = getattr(self, field)
            if is_var(v):
                ret.append((field, v))
        return ret

    def contain(self, v):
        """
        :type v: Var
        :rtype: bool
        """
        for f in FIELDS:
            _v = getattr(self, f)
            if _v == v:
                return f
        return ""

    def test(self, w):
        """
        :type w: rete.WME
        """
        for f in FIELDS:
            v = getattr(self, f)
            if is_var(v):
                continue
            if v != getattr(w, f):
                return False
        return True


class WME:

    def __init__(self, identifier, attribute, value):
        self.identifier = identifier
        self.attribute = attribute
        self.value = value
        self.amems = []  # the ones containing this WME
        self.tokens = []  # the ones containing this WME
        self.negative_join_result = []

    def __repr__(self):
        return "(%s ^%s %s)" % (self.identifier, self.attribute, self.value)

    def __eq__(self, other):
        """
        :type other: WME
        """
        if not isinstance(other, WME):
            return False
        return self.identifier == other.identifier and \
            self.attribute == other.attribute and \
            self.value == other.value


class Token:

    def __init__(self, parent, wme, node=None):
        """
        :type wme: WME
        :type parent: Token
        """
        self.parent = parent
        self.wme = wme
        self.node = node  # points to memory this token is in
        self.children = []  # the ones with parent = this token
        self.join_results = []  # used only on tokens in negative nodes
        self.ncc_results = []
        self.owner = None  # NCC

        if self.wme:
            self.wme.tokens.append(self)
        if self.parent:
            self.parent.children.append(self)

    def __repr__(self):
        return "<Token %s>" % self.wmes

    def __eq__(self, other):
        return isinstance(other, Token) and \
               self.parent == other.parent and self.wme == other.wme

    def is_root(self):
        return not self.parent and not self.wme

    @property
    def wmes(self):
        ret = [self.wme]
        t = self
        while not t.parent.is_root():
            t = t.parent
            ret.insert(0, t.wme)
        return ret

    @classmethod
    def delete_token_and_descendents(cls, token):
        """
        :type token: Token
        """
        from rete.negative_node import NegativeNode
        from rete.ncc_node import NccPartnerNode, NccNode

        for child in token.children:
            cls.delete_token_and_descendents(child)
        if not isinstance(token.node, NccPartnerNode):
            token.node.items.remove(token)
        if token.wme:
            token.wme.tokens.remove(token)
        if token.parent:
            token.parent.children.remove(token)
        if isinstance(token.node, NegativeNode):
            for jr in token.join_results:
                jr.wme.negative_join_results.remove(jr)
        elif isinstance(token.node, NccNode):
            for result_tok in token.ncc_results:
                result_tok.wme.tokens.remove(result_tok)
                result_tok.parent.children.remove(result_tok)
        elif isinstance(token.node, NccPartnerNode):
            token.owner.ncc_results.remove(token)
            if not token.owner.ncc_results:
                for child in token.node.ncc_node.children:
                    child.left_activation(token.owner, None)


class NCCondition:

    def __init__(self, cond_list):
        """
        :type cond_list: list of Condition
        """
        self.cond_list = cond_list

    @property
    def number_of_conditions(self):
        return len(filter(lambda x: isinstance(x, Condition), self.cond_list))


def is_var(v):
    return v.startswith('$')


def op(v):
    if v.startswith('>') or v.startswith('<'):
        return OP_COMPARE
    return OP_EQUAL
