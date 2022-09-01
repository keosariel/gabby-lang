from src.pparser.Lexer import PLexer
import src.pparser.utils as utils
from sly import Parser
import pprint

class PParser(Parser):
    tokens = PLexer.tokens

    precedence = (
        ('nonassoc', NE, LT, LE, GT, GE, EQEQ, XOR, OR),
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
        ('left', LSHIFT, RSHIFT),
    )

    def __init__(self):
        self.ast = ('Module',{'body':[]})
    
    @_("statements")
    def body(self, p):
        self.ast[1]['body'] = p.statements

    
    @_('statement')
    def statements(self, p):
        return [p.statement]

    @_('statements statement')
    def statements(self, p):
        p.statements.append(p.statement)
        return p.statements
    
    @_('RETURN expr')
    def statement(self,p):
        return ('Return',{'value':p.expr})
    
        
    @_('DEF NAME LPAREN def_params RPAREN COLON NAME LBRACE statements RBRACE')
    def statement(self,p):
        return utils.function(p.NAME0,p.def_params,p.NAME1,p.statements)
    
    @_('IF expr LBRACE statements RBRACE')
    def statement(self,p):
        return utils.if_stmt(p.statements,orelse=[],test=p.expr)
    
    @_('IF expr LBRACE statements RBRACE ELSE LBRACE statements RBRACE')
    def statement(self,p):
        return utils.if_stmt(p.statements0,p.statements1,p.expr)
    
    @_('WHILE expr LBRACE statements RBRACE')
    def statement(self,p):
        return utils.while_block(p.statements,p.expr)
    
    @_('UNTIL expr LBRACE statements RBRACE')
    def statement(self,p):
        return utils.until_block(p.statements,p.expr)
    
    @_('NAME EQ expr')
    def statement(self,p):
        return utils.var_assign(p.NAME,p.expr)
    
    @_('NAME LPAREN params RPAREN')
    def statement(self,p):
        return utils.func_call(p.NAME,p.params)
    
    @_('def_params COMMA def_param')
    def def_params(self,p):
        p.def_params.append(p.def_param)
        return p.def_params
    
    @_('def_param')
    def def_params(self,p):
        return [p.def_param]
    
    @_('NAME COLON NAME')
    def def_param(self,p):
        return {'name':p.NAME0,'type':p.NAME1}
    
    @_('')
    def def_param(self,p):
        return
    
    @_('params COMMA param')
    def params(self,p):
        p.params.append(p.param)
        return p.params
    
    @_('param')
    def params(self,p):
        return [p.param]
    
    @_('expr')
    def param(self,p):
        return p.expr
    
    @_('')
    def param(self,p):
        return
    
    @_('NAME LPAREN params RPAREN')
    def expr(self,p):
        return utils.func_call(p.NAME,p.params)
    
    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr DIVIDE expr',
       'expr MOD expr',
       'expr LSHIFT expr',
       'expr RSHIFT expr',
       'expr GT expr',
       'expr GE expr',
       'expr LT expr',
       'expr LE expr',
       'expr NE expr',
       'expr EQEQ expr',
       'expr AND expr',
       'expr OR expr')
    def expr(self,p):
        return utils.expression(p[1],p.expr0,p.expr1)
    
    
    @_('LPAREN expr RPAREN')
    def expr(self,p):
        return p.expr

    @_('NAME')
    def expr(self,p):
        return utils.data('Name',p.NAME)
    
    @_('NUMBER')
    def expr(self,p):
        return utils.data('Number',int(p.NUMBER))
    
    @_('MINUS NUMBER')
    def expr(self,p):
        return utils.data('Number',int(p.NUMBER)*-1)
    
    @_('FLOAT')
    def expr(self,p):
        return utils.data('Float',float(p.FLOAT))
        
    @_('MINUS FLOAT')
    def expr(self,p):
        return utils.data('Float',float(p.FLOAT)*-1)
    
    @_('STRING')
    def expr(self,p):
        return utils.data('String',p.STRING)
