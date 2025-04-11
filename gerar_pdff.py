import mysql.connector
from fpdf import FPDF

class PDFCotacao(FPDF):
    def header(self):
        self.set_fill_color(25, 42, 86)
        self.rect(0, 0, 210, 25, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 15, 'COMMERCIAL ', 0, 1, 'C')
        self.ln(10)

    def section_title(self, title):
        self.set_fill_color(169, 169, 169)  # cinza escuro
        self.set_text_color(255)
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 8, title, 0, 1, 'L', fill=True)
        self.set_text_color(0)
        self.ln(1)

    def field(self, label, value):
        self.set_text_color(90)
        self.set_font('Helvetica', '', 10)
        self.cell(40, 7, f"{label}", 0, 0)
        self.set_text_color(0)
        self.set_font('Helvetica', 'B', 10)
        if isinstance(value, str):
            value = value.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 7, str(value))

    def draw_table_header(self):
        self.set_fill_color(169, 169, 169)
        self.set_text_color(255)
        self.set_font('Helvetica', 'B', 9)
        self.cell(80, 8, 'Service', 1, 0, 'L', 1)
        self.cell(30, 8, 'Currency', 1, 0, 'C', 1)
        self.cell(30, 8, 'Rate', 1, 0, 'C', 1)
        self.cell(30, 8, 'Unity', 1, 1, 'C', 1)
        self.set_text_color(0)

    def draw_table_row(self, service, currency, rate, unity):
        self.set_font('Helvetica', '', 9)
        self.cell(80, 7, service, 1)
        self.cell(30, 7, currency, 1, 0, 'C')
        self.cell(30, 7, f"{rate:.2f}", 1, 0, 'C')
        self.cell(30, 7, unity, 1, 1, 'C')

    def line_break(self):
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

def gerar_pdf_fpdf(numero_cotacao):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='user',
            password='senha',
            database='banco'
        )
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                Q.ID, Q.CODE, Q.DATE_REQUEST, Q.DATE_VALIDITY, Q.DATE_CREATION,
                Q.SUBJECT, Q.CLIENT_PO, Q.REF_CLIENT, Q.COMMODITY_DESCRIPTION,
                Q.FOOTER_COMMENTS, Q.TERM_COMMENTS,
                U.NAME_USER AS VENDEDOR, U.SMTP_USER,
                C.NAME_CG AS CLIENTE,
                CP.NAME_CP AS CONTATO, CP.DIRECT_PHONE,
                A.NAME_CG AS AGENTE, A.PHONE AS AGENTE_TEL, A.FEDERAL_REGISTRATION,
                AD.STREET_NAME, AD.COMPLEMENT, AD.CITY_NAME, AD.NEIGHBORHOOD,
                O.NAME_PORT AS ORIGEM, D.NAME_PORT AS DESTINO,
                INC.CODE AS INCOTERM
            FROM M0205_QUOTATION Q
            LEFT JOIN M0003_USER U ON Q.PRICING_USER_FK = U.ID
            LEFT JOIN M0130_CONTACT_GENERAL C ON Q.CLIENT_CONTACT_GENERAL_FK = C.ID
            LEFT JOIN M0130_CONTACT_PERSON CP ON Q.CONTACT_CUSTOM_BROKER_CG_FK = CP.ID
            LEFT JOIN M0130_CONTACT_GENERAL A ON Q.AGENT_CONTACT_GENERAL_FK = A.ID
            LEFT JOIN M0001_ADDRESS AD ON A.ADDRESS_FK = AD.ID
            LEFT JOIN M0105_MAPORT O ON Q.PORT_ORIGIN_FK = O.ID
            LEFT JOIN M0105_MAPORT D ON Q.PORT_DESTINATION_FK = D.ID
            LEFT JOIN M0107_INCOTERM INC ON Q.INCOTERM_FK = INC.ID
            WHERE Q.CODE = %s
        """

        cursor.execute(query, (numero_cotacao,))
        dados = cursor.fetchone()
        if not dados:
            return None

        quotation_id = dados['ID']

        cursor.execute("""
            SELECT 
                I.SERVICE_DESCRIPTION, I.SALE_TOTAL, I.RATE_TYPE,
                IFNULL(C.SYMBOL, '') AS MOEDA, IFNULL(M.CODE, '') AS UNIDADE
            FROM M0205_QUOTATION_ITEM I
            LEFT JOIN M0101_CURRENCY C ON I.BUY_CURRENCY_FK = C.ID
            LEFT JOIN M0103_MEASURE_UNIT M ON I.MEASURE_UNIT_FK = M.ID
            WHERE I.QUOTATION_FK = %s
        """, (quotation_id,))

        itens = cursor.fetchall()
        freight = [i for i in itens if i['RATE_TYPE'] == 'FREIGHT']
        origin = [i for i in itens if i['RATE_TYPE'] == 'ORIGIN']

        pdf = PDFCotacao()
        pdf.add_page()

        pdf.section_title("From")
        pdf.field("Nome", dados['VENDEDOR'])
        pdf.field("Email", dados['SMTP_USER'])
        pdf.line_break()

        pdf.section_title("To")
        pdf.field("Cliente", dados['CLIENTE'])
        pdf.line_break()

        pdf.section_title("A/C")
        pdf.field("Contato", dados['CONTATO'])
        pdf.field("Telefone", dados['DIRECT_PHONE'])
        pdf.line_break()

        pdf.section_title("Quotation")
        pdf.field("Reference", dados['CODE'])
        pdf.field("Request", dados['DATE_REQUEST'].strftime('%d/%m/%Y'))
        pdf.field("Validity", dados['DATE_VALIDITY'].strftime('%d/%m/%Y'))
        pdf.field("Send Date", dados['DATE_CREATION'].strftime('%d/%m/%Y'))
        pdf.line_break()

        pdf.section_title("Shipment")
        pdf.field("Assunto", dados['SUBJECT'])
        pdf.field("Origin", dados['ORIGEM'])
        pdf.field("Destination", dados['DESTINO'])
        pdf.field("P.O Cliente", dados['CLIENT_PO'])
        pdf.field("Client Reference", dados['REF_CLIENT'])
        pdf.field("Incoterm", dados['INCOTERM'])
        pdf.field("Commodity Description", dados['COMMODITY_DESCRIPTION'])
        pdf.line_break()

        pdf.section_title("Agent")
        pdf.field("Nome", dados['AGENTE'])
        pdf.field("CNPJ", dados['FEDERAL_REGISTRATION'])
        pdf.field("Telefone", dados['AGENTE_TEL'])
        endereco = f"{dados['STREET_NAME']}, {dados['COMPLEMENT']} - {dados['NEIGHBORHOOD']}, {dados['CITY_NAME']}"
        pdf.field("Endereço", endereco)
        pdf.line_break()

        if freight:
            pdf.section_title("International Freight")
            pdf.draw_table_header()
            for item in freight:
                pdf.draw_table_row(item['SERVICE_DESCRIPTION'], item['MOEDA'], item['SALE_TOTAL'], item['UNIDADE'])
            pdf.line_break()

        if origin:
            pdf.section_title("Origin Costs")
            pdf.draw_table_header()
            for item in origin:
                pdf.draw_table_row(item['SERVICE_DESCRIPTION'], item['MOEDA'], item['SALE_TOTAL'], item['UNIDADE'])
            pdf.line_break()

        pdf.section_title("Remarks")
        pdf.field("", dados['FOOTER_COMMENTS'])
        pdf.line_break()

        pdf.section_title("Terms and Conditions")
        pdf.field("", dados['TERM_COMMENTS'])

        caminho = f"cotacao_{dados['CODE']}.pdf"
        pdf.output(caminho)
        return caminho

    except Exception as e:
        print("Erro ao gerar PDF:", e)
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
