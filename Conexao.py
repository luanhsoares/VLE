# -*- coding: utf-8 -*-

from sqlite3 import connect
from warnings import warn
from scipy import exp, log
from scipy.optimize import root
from numpy import zeros

conector = connect('testeando.db')          # Conecta a rotina ao banco de dados
cursor   = conector.cursor()                # Permite a navegação no banco de dados a partir da rotina

class Componente_Caracterizar:
    
    def __init__(self,Componente,ConfigPsat=('Prausnitz4th',None),T=298.15):
        '''
        Algoritmo para caracterizar os componentes.
        '''
        self.__lista_EqPsat = ['Prausnitz4th'] # Lista dos métodos utilizados para o cálculo da pressão de vapor

        # COMPONENTE & ID
        self.Nome = Componente # Nome do componente
        self.Validacao_Nome()  # Verificar se o nome do componente está no banco
        self.Busca_ID()        # Busca do ID do componente e cria o atributo ID.

        # TEMPERATURA
        self.T    = T # Temperatura
        
        # PRESSÃO DE VAPOR
        self.EqPsat   = ConfigPsat[0] # Nome da equação para cálculo da pressão de vapor
        self.nEqPsat  = ConfigPsat[1] # Número da equação de Psat (Vide referência(?))
        
        self.Validacao_e_Default_de_EqPsat() # Validação dos atributos de pressão de vapor

        # PROPRIEDADES DO COMPONENTE PURO
        self.Propriedade() # Criação dos atributos contendo as propriedades do componentes puro
        


    def lista_componentes(self):
        '''
        Algoritmo para gerar uma lista contendo os nomes dos componentes disponíveis no banco de dados.
        
        =====
        Saída
        =====
        * Uma lista contendo os nomes dos componentes.
        '''        
        cursor.execute('SELECT Nome FROM Componentes')  # Seleciona a coluna Nome da tabela Componentes do banco de dados
        row = cursor.fetchall()                         # Retorna a coluna selecionada em forma de lista de tuplas
        return [i[0] for i in row]                      # Transforma a lista de tuplas em uma lista com o contéudo das tuplas (os nomes dos componentes)
        

    def Validacao_Nome(self):
        '''
        Subrotina para validar a entrada ``Componente``. Comparando esta entrada com os nomes obtidos pelo método ``lista_componentes``. Se a entrada de ``Componente`` não passam pela validação, há a emissão de um erro como saída deste método. O erro emitido interrompe a execuçao do programa.

        '''
        # Validação do nome do método de cálculo da pressão de vapor
        if self.Nome not in self.lista_componentes():                               
            raise NameError(u'O nome do componente não consta no banco de dados.')  # Emite um erro com a mensagem inserida no método
    
    def Busca_ID(self):
        '''
        Subrotina para busca do ID, chave primária, da tabela Componmentes no banco de dados.
        
        =====
        Saída
        =====
        
        * Gera a ID em forma de número inteiro. Esta saída é gerada como atributo da classe ``Componente_Caracterizar``.
        '''
        cursor.execute('SELECT ID FROM Componentes WHERE  Nome=?',(self.Nome,)) # Busca do ID do componente na tabela Componentes no banco de dados
        row = cursor.fetchall()                                                 # Retorna a linha contendo o ID em forma de lista de tupla
        self.ID = row[0][0]                                                     # Cria o atributo ID

    def Busca_FormaEqPsat(self):        
        '''
        Método para buscar a forma da equação para o cálculo de  Psat no banco de dados.
                
        =====
        Saída
        =====
        
        * A saída deste método é uma lista contendo as formas de equações, que são números inteiros, para o componente requerido.
        '''
        
        if self.EqPsat == self.__lista_EqPsat[0]: 
            cursor.execute('SELECT ID_forma FROM Parametros_Psat_Prausnitz_4th_edition WHERE ID_componente=?',(self.ID,)) # Busca as possíveis formas de equação do cálculo da pressão de vapor
            row = cursor.fetchall()         # Cria uma lista de tuplas contendo as formas de equações
        return [i[0] for i in row]          # Transforma a lista de tuplas em uma lista com o contéudo das tuplas (Os marcadores das formas de equações)

    def Validacao_e_Default_de_EqPsat(self):
        '''
        Este método valida as entradas de ``ConfigPsat``. Assim são validadas as entradas do método de cálculo de Psat e as formas de equações dos métodos. Se as entradas de ``ConfigPsat`` não passam pela validação, há a emissão de um erro como saída deste método. O erro emitido interrompe a execuçao do programa.
        
        '''
        # VALIDAÇÃO DO NOME DO MÉTODO DE CÁLCULO DE PRESSÃO DE VAPOR
        
        # Caso o método inserido não constar na lista de métodos disponíveis
        if self.EqPsat not in self.__lista_EqPsat:                      
            raise NameError(u'O método de cálculo de Psat não consta no banco de dados.') 
        # Caso o método inserido conste na lista de métodos disponíveis:
        if self.EqPsat == self.__lista_EqPsat[0]:
            dadosbanco = self.Busca_FormaEqPsat()   # Busca as formas de equações disponíveis do banco de dados
            if self.nEqPsat != None:                # Caso a forma da equação seja inserida pelo usuário
                if self.nEqPsat not in dadosbanco:  # Caso a forma da equação inserida não conste no banco
                    raise ValueError(u'Foi inserido um número de forma de equaçao que não consta no Banco de dados. Informaçao disponível:'+'%d,'*(len(dadosbanco)-1)+'%d.'%tuple(dadosbanco)) 
            
            if self.nEqPsat == None:                # Caso a forma da equação não seja inserida
                if len(dadosbanco) == 1:            # Caso haja apenas uma forma de equação, dados banco tem tamanho 1
                    self.nEqPsat = dadosbanco[0]    # Como não seja inserida a forma de equação, o programa usará a única forma disponível
                else: # Caso haja mais de uma forma de equação disponível no banco de dados
                    raise ValueError(u'É necessário informar expressamente a forma da equaçao, dado que há mais opções disponíveis.'+'%d,'*len(dadosbanco)%tuple(dadosbanco)) 
        
        
    def warnings(self):
        '''        
        Método para verificar se a temperatura inserida está dentro ou não da faixa de aplicação das fórmulas do calculo da pressão de vapor. Caso não esteja dentro da faixa de aplicabilidade, o programa gerará um aviso. Contudo a execução não será interrompida.
        
        '''
        # Verificação se a temperatura inserida está dentro ou não da faixa de aplicabilidade das fórmulas do cálculo de Psat
        if self.T < self.__TminPsat or self.T > self.__TmaxPsat:
            warn(u'A temperatura especificada está fora do range de aplicabilidade da equaçao de Psat') # Emite um aviso com a mensagem inserida no método. Contudo o programa continua a rodar
  


    def Pvap_Prausnitz_4th(self,VPA,VPB,VPC,VPD,T,nEq,Tc=None,Pc=None,Pvp_ini=101325,tol=1e-10):
        '''
        Método para cálculo da pressão de vapor de componentes puros, conforme [1].
        
        ========
        Entradas
        ========
        
        * VPA (float): Parâmetro VPA;
        * VPB (float): Parâmetro VPB;
        * VPC (float): Parâmetro VPC;
        * VPD (float): Parâmetro VPD;
        * T (float): Temperatura em Kelvin;
            
            * O valor de T inserido deve ser menor do que o valor de Tc.
        * nEq (int): Número de identificação da forma (ou tipo) de equação;
        * Tc (float): Temperatura crítica em Kelvin; 
        * Pc (float): Pressão crítica em bar
        * Pvp_ini: Estimativa inicial para a pressão de vapor, quando nEq = 2 (Equação implícta).
        * tol: teolerância para o cálculo da raiz da equação nEq = 2 (Equação implícta)
        
        ================
        Valores default 
        ================        
        
        Valores utilizados apenas quando nEq = 2.
        
        * Pvp_ini = 101325 bar
        * tol     = 1e-10
        
        =====
        Saída
        =====
        
        * Retorna a pressão de vapor em bar
        
        =========
        Refeência
        =========
        
        [1] REID, R.C.; PRAUSNITZ, J.M.; POLING, B.E. The properties of Gases and Liquids, 4th edition, McGraw-Hill, 1987.
        '''
    
        # Equação implícita para cálculo de Psat para nEq = 2
        def Eq2(Pvp,VPA,VPB,VPC,VPD,T): 
            Res = VPA - VPB/T + VPC*log(T) + VPD*Pvp/(T**2.0)-log(Pvp) # Vide [1]
            return Res
    
        if self.nEqPsat == 1: # Cálculo de Psat quando nEq = 1
            Pc  = Pc # Bar
            x   = 1 - T/Tc
            Pvp = exp((VPA*x+VPB*(x**1.5)+VPC*(x**3.0)+VPD*(x**6.0))/(1.0-x))*Pc # Vide [1]
            # P.s.: Caso o T inserido seja maior que o valor de Tc, haverá um erro.
            
        elif self.nEqPsat == 2:  # Cálculo de Psat quando nEq = 2
            Pvp_ini = Pvp_ini # Bar, Estimativa inicial
            Resul   = root(Eq2,Pvp_ini,args=(VPA,VPB,VPC,VPD,T),tol=tol) # Determinação das raízes da equação implícia
            return Resul.x # Retorno
    
        elif self.nEqPsat == 3: # Cálculo de Psat quando nEq = 3
           Pvp = exp(VPA-VPB/(T+VPC)) # Vide [1]
    
        # Todos os Pvp são dados em bar
        return Pvp


    def Propriedade(self):
        '''
        Algoritmo para busca das propriedades dos componentes puros.
        
        ======        
        Saídas
        ======
        * Todas as propriedades que sao buscadas retornam em forma de atributos do tipo float. As propriedades que são selecionadas por este algoritmo são:
            
            * Temperatura crítica em Kelvin;
            * Pressão crítica em bar;
            * Fator acêntrico (Adimensional);
            * Massa molar em g.mol-1;
            * Raio médio de giração (Adimensional) ;
            * Fator de compressibilidade crítico (Adimensional) ;
            * Volume molar crítico (Adimensional) ;
            * Momento dipolo (Adimensional)
            * Parâmetros do modelo UNIQUAC (Adimensionais);
            * Parâmetros para o cálculo de Psat, vide [1];
            * Temperatura mínima para a aplicaçao da fórmula do cálculo de Psat;
            * Temperatura máxima para a aplicaçao da fórmula do cálculo de Psat;
            * Densidade do líquido;
            * Temperatura da densidade do líquido.
            
        =========
        Refeência
        =========
        
        [1] REID, R.C.; PRAUSNITZ, J.M.; POLING, B.E. The properties of Gases and Liquids, 4th edition, McGraw-Hill, 1987.
        '''
        
        cursor.execute('SELECT * FROM Propriedades_puras WHERE  ID_componente=?',(self.ID,))
        row = cursor.fetchall() # linha do banco de dados para o ID

        # PROPRIEDADES DA SUBSTÂNCIA (Tc,Pc,Fator acêtrico(w),Massa molar (MM),radius_giration,Fator de Compressibilidade crítico(Zc)
        #                             ,Volume molar crítico(Vc),dipole_moment,Parâmetros do UNIQUAC(r,q & ql),d & Td)
        
        self.Tc              = row[0][2]  # Temperatura crítica / K
        self.Pc              = row[0][3]  # Pressão crítica / bar
        self.w               = row[0][4]  # Fator acêtrico / admnesional
        self.MM              = row[0][5]  # Massa Molar
        self.radius_giration = row[0][6]  # mean Radius of gyration
        self.Zc              = row[0][7]  # Fator de Compressibilidade crítico
        self.Vc              = row[0][8]  # Volume molar crítico
        self.dipole_moment   = row[0][9]  # Momento dipolo
        self.r               = row[0][10] # Parâmetro r do UNIQUAC
        self.q               = row[0][11] # Parâmetro q do UNIQUAC
        self.ql              = row[0][12] # Parâmetro ql do UNIQUAC (Correção para álcool)
        self.d               = row[0][13] # Densidade líquido
        self.Td              = row[0][14] # Temp_Densidade líquido

        # PARÂMETROS DO CÁLCULO DE PRESSÃO DE VAPOR (The Properties of Gases & Liquids, 4th edition)
        
        if self.EqPsat == self.__lista_EqPsat[0]:
            cursor.execute('SELECT * FROM Parametros_Psat_Prausnitz_4th_edition WHERE  ID_componente=? AND ID_forma=?',(self.ID,self.nEqPsat))
            row = cursor.fetchall() 
            
            # PARÂMETROS PARA O CÁLCULO DE PSAT FORNECIDO PELO Prausnitz_4th_edition 
            
            self.VPA             = row[0][3]
            self.VPB             = row[0][4]
            self.VPC             = row[0][5]
            self.VPD             = row[0][6]
            
            # FAIXA DE TEMPERATURA NA QUAL PODE-SE APLICAR OS CÁLCULOS DE PSAT
            
            self.__TminPsat = row[0][7]  #  Temperatura mínima de Psat  
            self.__TmaxPsat = row[0][8]  #  Temperatura máxima de Psat
            
            # PARTE A SER FINALIZADA!!!!!!!!!!!!!!!!
            self.warnings()    
            self.Psat = self.Pvap_Prausnitz_4th(self.VPA,self.VPB,self.VPC,self.VPD,self.T,self.nEqPsat,self.Tc,self.Pc)

class Modelo:

    def __init__(self,Componentes):
        '''
        Componentes é uma lista de objeto componentes
        '''
        self.__ID_Componentes = [Componente.ID for Componente in Componentes] # Criação da lista com as ID's dos componentes
 
        
    def Propriedade_mistura(self,coluna,tabela,IDFORMA=False):
        '''
        Documentação
        '''
        
        retorno = zeros((len(self.__ID_Componentes),len(self.__ID_Componentes))).tolist() # Criação da matriz de zeros em forma de lista de listas
        # Substituição dos elementos da matriz criada
        for i,ID_i in enumerate(self.__ID_Componentes):
            for j,ID_j in enumerate(self.__ID_Componentes):
                if IDFORMA == False:
                    selecao = 'SELECT '+coluna+' FROM '+tabela+' WHERE ID_componente_i=? AND ID_componente_j=? '
                else:
                    selecao = 1
                cursor.execute(selecao,(ID_i,ID_j))
                row = cursor.fetchall() 
                retorno[i][j] = row[0][0]
        return retorno


class VIRIAL(Modelo):
   
    def __init__(self,Componentes,regra_mistura='Hayden_o_Connel'):
        '''
        Componentes é uma lista de objeto componentes
        '''
        
        Modelo.__init__(self,Componentes)
        self.nome = 'VIRIAL'
        self.coef_solv = self.Propriedade_mistura('CoeficienteSolvatacao','Propriedade_mistura')                                            # Trasforma a def Propriedade_mistura em atributo da classe Propriedade_Mistura
        
    def ValidacaoREGRA(self):
        '''
        docuemn
        '''
        self.__regras_mistura_disponiveis = ['Hayden_o_Connel','Tsonopoulos']
        
    
    # Validar
        
        
#class Modelos(Propriedade_Mistura):
#    
#    def Model_Therm(self):
#        if self.model == 'NRTL':
#            s = (self.ID[0],self.ID[1],)
#            c.execute('SELECT * FROM NRTL WHERE ID_componente_i=? AND ID_componente_j=? ',s)
#            row = c.fetchall()
#            for i in xrange(len(row)):
#                if self.forma == row[0][3]:
#                    # Parâmetro de interação:
#                    self.P_i = row[0][6]
#                    # Parâmetro de não aleatoriedade                    
#                    self.alpha = row[0][7]
#                    
#        elif self.model == 'UNIQUAC':        
#            s = (self.ID[0],self.ID[1],)
#            c.execute('SELECT * FROM UNIQUAC_parametros_interecao_binaria WHERE ID_componente_i=? AND ID_componente_j=? ',s)
#            row = c.fetchall()
#            for i in xrange(len(row)):
#                if self.forma == row[0][3]:
#                    # Parâmetro de interação:
#                    self.P_i = row[0][6]
#        
#        elif self.model == 'Van Laar':
#            s = (self.ID[0],self.ID[1],)
#            c.execute('SELECT * FROM Van_Laar WHERE ID_componente_i=? AND ID_componente_j=? ',s)
#            row = c.fetchall()
#            # Parâmetro A:
#            self.A = row[0][3]
#            # Parâmero B
#            self.B = row[0][4]
#                   
#        elif self.model == 'Wilson':
#            s = (self.ID[0],self.ID[1],)
#            c.execute('SELECT * FROM Wilson WHERE ID_componente_i=? AND ID_componente_j=? ',s)
#            row = c.fetchall()
#            for i in xrange(len(row)):
#                if self.forma == row[0][3]:
#                    # Parâmetro de interação:
#                    self.P_i = row[0][6]
#        
#    def EoS(self):
#        if self.Eq == 'Peng-Robinson':
#            s = (self.ID[0],self.ID[1],)
#            c.execute('SELECT * FROM Peng-Robinson WHERE ID_componente_i=? AND ID_componente_j=? ',s)
#            row = c.fetchall()
#            # Parâmetro k:
#            self.k = row[0][3]
#
#        elif self.Eq == 'SRK':
#            s = (self.ID[0],self.ID[1],)
#            c.execute('SELECT * FROM SRK WHERE ID_componente_i=? AND ID_componente_j=? ',s)
#            row = c.fetchall()
#            # Parâmetro k:
#            self.k = row[0][3]
#            
            
            
Comp1 = Componente_Caracterizar('Metano',ConfigPsat=('Prausnitz4th',1),T=100.0)
Comp2 = Componente_Caracterizar('Etano',ConfigPsat=('Prausnitz4th',1),T=289.9)


PM = VIRIAL([Comp1,Comp2])

PM.coef_solv