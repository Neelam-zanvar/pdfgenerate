import os
import sys
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image ,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
import json
from reportlab.platypus import Spacer
from datetime import datetime  # Import datetime module
import mysql.connector

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def read_config_value(config_file, key):
    # Read the value of a specific key from the configuration file
    with open(config_file, 'r') as f:
        for line in f:
            if line.strip().startswith(key):
                return line.strip().split('=')[1].strip()
    return None

def fetch_data_from_db():
    config = {}
    with open('config.txt') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key.strip().lower()] = value.strip()  # Map keys to lowercase

    groupid = read_config_value('config.txt', 'GROUP_ID')
    sql_query = f"""
    SELECT value FROM history_text ht
    WHERE itemid IN (
        SELECT itemid FROM items i
        WHERE name='HardwareAuditResult' AND hostid IN (
            SELECT hosts.hostid AS hostid FROM hosts
            JOIN hosts_groups hg ON hosts.hostid = hg.hostid
            JOIN host_tag ON hosts.hostid = host_tag.hostid
            WHERE hg.groupid = {groupid} AND tag='Service' AND value ='Audit'
        )
    )
    ORDER BY clock DESC
    LIMIT 1
    """

    sql_query2 = f"""
    SELECT value FROM history_text ht
    WHERE itemid IN (
        SELECT itemid FROM items i
        WHERE name='SoftwareAuditResult' AND hostid IN (
            SELECT hosts.hostid AS hostid FROM hosts
            JOIN hosts_groups hg ON hosts.hostid = hg.hostid
            JOIN host_tag ON hosts.hostid = host_tag.hostid
            WHERE hg.groupid = {groupid} AND tag='Service' AND value ='Audit'
        )
    )
    ORDER BY clock DESC
    LIMIT 1
    """

    sql_query3 =f"""
           select name from hstgrp h where groupid = {groupid}
              """

    try:
        connection = mysql.connector.connect(
            host=config['db_host'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )

        if connection.is_connected():
    

            cursor = connection.cursor()
            cursor.execute(sql_query)
            result = cursor.fetchone()
            json_data = json.loads(result[0]) if result else {}

            cursor.execute(sql_query2)
            result2 = cursor.fetchone()
            json_data2 = json.loads(result2[0]) if result2 else {}

            cursor.execute(sql_query3)  
            result3 = cursor.fetchone() 
            if result3:
                host_name = result3[0]                  
            else:
                print("No data found for query 3")

            return json_data, json_data2, host_name

    except mysql.connector.Error as error:
        print("Error while connecting to MySQL database:", error)
        return {}, {}

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
        

def pageNumber(canvas, doc,title=None,total_pages=None,config_file='config1.txt'):
         
        page_number = canvas.getPageNumber()        
        text = f"Page {page_number}"
        canvas.drawRightString(830, 35, text)  # Adjust coordinates as needed
        canvas.drawString(330, 35, "Minutus computing confidential")
        # Read the company name from the configuration file
       # company_name = read_config_value(config_file, 'company_name')
        canvas.drawString(330, 570, " Software & Hardware Audit Report")  # Adjust coordinates as needed 
        
        # # Check if a title is provided and draw it
        # if title and total_pages and page_number == total_pages:
        #       canvas.drawString(400, 530, title)   
         # Add current date and time on the first title page
        # if page_number == 2:
        now = datetime.now()
        current_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        font_size = 9  # Adjust the font size as needed
        canvas.setFont("Helvetica", font_size)      
        canvas.drawString(339, 20, f"Generated on: {current_datetime}") 

        canvas.line(0, 60, 900, 60)
        canvas.line(0, 550, 900, 550)
        logo_path = resource_path('logo1.jpg')  # Provide the path to your logo image
        logo = Image(logo_path, width=50, height=45)  # Adjust width and height as needed
        logo.drawOn(canvas, 793, 551)  # Adjust position as needed
        
        

def generate_pdf(json_data,  json_data2,path,image,last_page_title=None):
    # Create a PDF document
    doc = SimpleDocTemplate(path, pagesize=landscape(A4))
    story = []
    page_titles = []
    section_start_pages = {}

    
    # Define styles
    styles = getSampleStyleSheet()
    center_style = styles["BodyText"]
    center_style.alignment = 1  # Center alignment
    bold_center_style = ParagraphStyle(name='BoldCenter', parent=center_style, fontName='Helvetica-Bold')
    bold_center_style1 = ParagraphStyle(name='BoldCenter', parent=center_style, fontName='Helvetica-Bold', fontSize=14)  # Increase font size here
    
     # Function to generate the title page
    def generate_title_page():
        title = resource_path("title1.png")
        image = Image(title, width=800, height=430)
        story.append(image)
        # text_on_first_page="this is a title page"
        # text_style = ParagraphStyle(name='TextOnFirstPage', parent=center_style, fontSize=12)
        # story.append(Paragraph(text_on_first_page, text_style))
        story.append(PageBreak())
        

    def add_section_title(title):
        page_titles.append(title)
        story.append(Paragraph(title, bold_center_style1))
        story.append(Spacer(1, 15))
        # section_start_pages[title] = len(story)
        # print(section_start_pages[title])
        

    def generate_table_of_contents():
        toc_style = ParagraphStyle(name='TOC', fontSize=16, leading=16)
        # Add the title
        toc_style1=ParagraphStyle(name='TOC', parent=center_style, fontSize=22, leading=16,fontName='Helvetica-Bold')
        story.append(Paragraph("Table of Contents",toc_style1))
        story.append(Spacer(1, 20))
        
        # Add entries for Architecture Diagram, Software Audit Report, and Hardware Audit Report
        entries = [
        ("Architecture Diagram", "1. Architecture Diagram"),
        ("Hardware Audit Report", "2. Hardware Audit Report"),
        ("Software Audit Report", "3. Software Audit Report")
       ]
        # Generate entries and page numbers
        page_number = 1
        for entry, section_title in entries:
            # text = f'{page_number}. <a href="{section_title}">{entry}</a>'
            toc_entry = Paragraph(section_title,toc_style)
            toc_entry.alignment = 0  # Left alignment
            story.append(Spacer(1, 15))
            story.append(toc_entry)
            story.append(Spacer(1, 5)) 
            page_number += 1
        
        story.append(Spacer(1, 290))
        
        
    def generate_content_pages():    
            def generate_table1():
                
                add_section_title("Hardware Audit Report")
                
                # hardware_audit_style = ParagraphStyle(name='HardwareAudit', parent=center_style, fontName='Helvetica-Bold', fontSize=14)
                # # Add the "Software Audit" text to the story using the defined style
                # story.append(Paragraph("Hardware Audit Report", hardware_audit_style))
                # story.append(Spacer(1, 15))
                # Define the table data
                data = [['Host\nName', 'CPU Information',"","","","","Memory\nInfo.", "Storage \n Information","Netwok Information"],
                        ['', 'Archit\necture', 'CPU\nCount', 'Vendor', 'Model', 'Cache','Total','Label & Drive','TCP Ports', 'UDP Ports', 'Adapters']]
                
                # Loop through each host in the JSON data
                for host_name, host_info in json_data.items():
                    
                    cpu_info = host_info.get("cpuInformation", {})
                    mem_info = host_info.get("memInformation", {})
                    storage_info = host_info.get("storageInformation", {})
                    network_info = host_info.get("networkInformation", {})

                    architecture = cpu_info.get("Architecture", "")
                    cpu_count = str(cpu_info.get("CPU Count", ""))
                    vendor = cpu_info.get("Vendor", "")
                    model = cpu_info.get("Model", "")
                    cache = cpu_info.get("Cache", "")
                    total_memory = mem_info.get("Total", "")

                    # Check if "Label" exists and get its data
                    label_info = storage_info.get("Label", {})
                    # Get data for "xvda" from the label_info dictionary
                    xvda_info = label_info.get("xvda", {})
                    # Add data for "xvda" to the storage_data list
                    storage_data = [f"xvda=> Size - {xvda_info.get('size', '')}, Available - {xvda_info.get('available', '')} , IOPS - {xvda_info.get('iops', '')} "]
                    # Other keys
                    for key, info in storage_info.items():
                        if key != "Label" and key != "xvda":
                            storage_data.append("\n" f"{key}=> Size - {info.get('size', '')}, Used - {info.get('used','')}   , Available - {info.get('available', '')} \n")

                    tcp_ports = ', '.join(network_info.get("TCP Ports", []))
                    udp_ports = ', '.join(network_info.get("UDP Ports", []))
                    Adapters = '\n'.join([f"{k}=>{v}" for k, v in network_info.get("Adapters", {}).items()])


                    # Create Paragraphs for each cell
                    host_name_paragraph = Paragraph(host_name, bold_center_style)
                    # cpu information
                    architecture_paragraph = Paragraph(architecture, center_style)
                    cpu_count_paragraph = Paragraph(cpu_count, center_style)
                    vendor_paragraph = Paragraph(vendor, center_style)
                    model_paragraph = Paragraph(model, center_style)
                    cache_paragraph = Paragraph(cache, center_style)
                    # memory information
                    total_memory_paragraph = Paragraph(total_memory, center_style)
                    # Storage information
                    storage_data_paragraph = Paragraph('\n'.join(storage_data))
                    # Network information
                    TCP_paragraph = Paragraph(tcp_ports, center_style)
                    UDP_paragraph = Paragraph(udp_ports, center_style)
                    Adapters_paragraph = Paragraph(Adapters)
                    # Add host name and CPU information to the table data
                    data.append([host_name_paragraph, architecture_paragraph, cpu_count_paragraph,
                                vendor_paragraph, model_paragraph, cache_paragraph, total_memory_paragraph,
                                storage_data_paragraph,TCP_paragraph,UDP_paragraph,Adapters_paragraph ])
                
                # Create the table
                table = Table(data, colWidths=[47, 45, 39, 47, 78, 45, 51, 105 , 90, 65,150], repeatRows=2)
                
                # Apply styles to the table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 1), colors.white),  # Gray background for header row
                    ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),  # White text color for header row
                    ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, 2), (-1, -1), colors.white),  # White background for data rows
                    ('TEXTCOLOR', (0, 2), (-1, -1), colors.black),  # Black text color for data rows
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center alignment for all cells
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Middle vertical alignment for all cells
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add gridlines to all cells
                    ('SPAN', (1, 0), (5, 0)),  # Merge cells from column 1 to 5 in the first row
                    ('SPAN', (0, 0), (0, 1)),  # Merge cells in the first column from row 1 to row 2
                    ('SPAN', (8, 0), (10, 0)),# Merge cells from column 8 to 9 in the first row
                    # ('SPAN', (10, 0), (12, 0)),  # Merge cells from column 10 to 12 in the first row
                    # ('SPAN', (13, 0), (13, 1)),  # Merge cells in the last column from row 1 to row 2
                    ('SPLITBYROWACTION', (1, 1), (-1, -1), 'SPLIT'),  # Split cell content if it exceeds cell width
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),  # Black text color for all cells
                ]))

                # Add the table to the story
                story.append(table)
                # Record the starting page number for Hardware Audit Report
                
                story.append(PageBreak())

            def generate_table2(): 
                
                add_section_title("Software Audit Report")
                # software_audit_style = ParagraphStyle(name='SoftwareAudit', parent=center_style, fontName='Helvetica-Bold', fontSize=14)
                # # Add the "Software Audit" text to the story using the defined style
                # story.append(Paragraph("Software Audit Report", software_audit_style))
                # story.append(Spacer(1, 15)) 


                table_data = [["Service", "Web server", "Tomee","", "Java"],
                        ["", "Version", "Version","Path", "Version", "Path"]]
                
                # software_audit_text = "Software Audit"
                # story.append(Paragraph(software_audit_text, bold_center_style1))
                for service, details in json_data2.items():
                    web_server_version = ""
                    tomee_version = ""
                    tomee_path= ""
                    java_version = ""
                    java_path = ""

                    if "Webserver" in details:
                        web_server_version = details["Webserver"]["Version"]

                    if "tomee" in details:
                        tomee_version = details["tomee"]["Version"]
                        # tomee_path = details["tomee"]["Path"]

                    if "java" in details:
                        java_version = details["java"]["Version"]
                        java_path = details["java"].get("Path", "")

                    # Create paragraph objects with word wrap
                    web_server_version_para = Paragraph(web_server_version, center_style)
                    tomee_version_para = Paragraph(tomee_version, center_style)
                    tomee_path_para = Paragraph(tomee_path, center_style)
                    java_version_para = Paragraph(java_version, center_style)
                    java_path_para = Paragraph(java_path, center_style)

                    table_data.append([service, web_server_version_para, tomee_version_para,tomee_path_para, java_version_para, java_path_para])

                table_style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.white),
                                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
                                        ('FONTSIZE', (0, 0), (-1, 1), 10),  # Increase font size for header
                                        ('BACKGROUND', (0, 2), (-1, -1), colors.white),  # White background for data rows
                                        ('TEXTCOLOR', (0, 2), (-1, -1), colors.black),
                                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),                              
                                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                        ('SPAN', (0, 0), (0, 1)),  # Merge cells in the first column from row 1 to row 2
                                        ('SPAN', (4, 0), (5, 0)),
                                        ('SPAN', (2, 0), (3, 0)),
                                        ('WORDWRAP', (1, 2), (-1, -1)),  # Allow word wrap for content
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])  # Vertical alignment

                # Manually set column widths
                col_widths = [190, 100, 135,160, 100, 100]  # Adjust the values as needed

                table = Table(table_data, colWidths=col_widths, repeatRows=2)
                table.setStyle(table_style)
                story.append(table)
                
            # Function to insert images into the PDF
            
              # Set the page size to A4 in landscape mode
            generate_table1()
            # section_start_pages["Hardware Audit Report"] = len(story)
            generate_table2()
            # section_start_pages["Software Audit Report"] = len(story)
            
     # Generate the title page
    generate_title_page()
    # Generate the content pages
    # generate_table_of_contents()
    def insert_images(image_paths):
                add_section_title("Architecture Diagram")
                # software_audit_style = ParagraphStyle(name='Images', parent=center_style, fontName='Helvetica-Bold', fontSize=14)
                #         # Add the "Software Audit" text to the story using the defined style
                # story.append(Paragraph("Architecture Diagram", software_audit_style))
                story.append(Spacer(1, 12))
                for path in image_paths:
                    
                    image = Image(path, width=820, height=400)
                    story.append(image)
                    story.append(PageBreak())
    insert_images(image_paths)
    
    generate_content_pages()  
    total_pages = len(story)     

    def generate_page_numbers(canvas, doc):
        page_number = canvas.getPageNumber()
        text = f"Page {page_number}"
        
        
        
    
    # Build the document
    if last_page_title:
        doc.build(story, onFirstPage=lambda canvas, doc:generate_page_numbers(canvas, doc),
                  onLaterPages=lambda canvas, doc: pageNumber(canvas, doc, last_page_title, total_pages))
        print("pdf is generated")
    else:
        doc.build(story, onFirstPage=lambda canvas, doc: generate_page_numbers(canvas, doc,section_start_pages),
                  onLaterPages=generate_page_numbers)   
        print("pdf is generated")

#image_paths = ["/var/www/html/php-files/3DXP-24x-crop.jpg"]  # Add as many image paths as needed
# with open("data.json", "r") as file1, open("parameter_audit.json", "r") as file2:
#     json_data = json.load(file1)
#     json_data2 = json.load(file2)
image_path_prefix = read_config_value('config.txt', 'IMAGE_PATH_PREFIX')
image_name=read_config_value('config.txt', 'IMAGE_NAME')
image_pathss = f"{image_path_prefix}{image_name}"
image_paths=[image_pathss]
json_data, json_data2,host_name = fetch_data_from_db()
# pdf_filename = f"{host_name}_audit_report.pdf"
generate_pdf(json_data, json_data2, f"{host_name}_audit_report.pdf", image_paths,last_page_title="Host Map")
