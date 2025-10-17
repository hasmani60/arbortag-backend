from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from io import BytesIO
import tempfile
import os

class ReportGenerator:
    def __init__(self, analyzer, visualizer):
        self.analyzer = analyzer
        self.visualizer = visualizer
        
    def generate_pdf_report(self, location: str = None) -> BytesIO:
        """Generate comprehensive PDF report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0f544b'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#27ae60'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = f"Tree Census Report - {location if location else 'All Locations'}"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Date
        date_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        stats = self.analyzer.get_statistics()
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Trees Tagged', f"{stats['total_trees']}"],
            ['Total Carbon Sequestration', f"{stats['total_carbon']:.2f} kg CO₂/year"],
            ['Total Oxygen Production', f"{stats['total_oxygen']:.2f} kg/year"],
            ['Average Tree Height', f"{stats['avg_height']:.2f} meters"],
            ['Average Tree Width', f"{stats['avg_width']:.2f} meters"],
            ['Number of Locations', f"{stats['total_locations']}"],
            ['Number of Species', f"{stats['total_species']}"],
            ['Most Common Species', stats['most_common_species']],
            ['Most Carbon Efficient', stats['most_carbon_efficient']],
        ]
        
        table = Table(summary_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f544b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        
        story.append(table)
        story.append(PageBreak())
        
        # Species Analysis
        story.append(Paragraph("Species Analysis", heading_style))
        species_dist = self.analyzer.get_species_distribution()
        
        story.append(Paragraph(
            f"A total of {len(species_dist)} different species were recorded. "
            f"The most abundant species is {stats['most_common_species']}, "
            f"representing a significant portion of the urban forest canopy.",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Top 5 species table
        top_species = sorted(species_dist.items(), key=lambda x: x[1], reverse=True)[:5]
        species_table_data = [['Species', 'Count', 'Percentage']]
        total_trees = stats['total_trees']
        
        for species, count in top_species:
            percentage = (count / total_trees) * 100
            species_table_data.append([species, str(count), f"{percentage:.1f}%"])
        
        species_table = Table(species_table_data, colWidths=[3*inch, 1*inch, 1*inch])
        species_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(species_table)
        story.append(PageBreak())
        
        # Carbon Impact
        story.append(Paragraph("Environmental Impact", heading_style))
        
        carbon_text = f"""
        The trees surveyed sequester a total of {stats['total_carbon']:.2f} kg of CO₂ per year,
        which is equivalent to offsetting the carbon emissions of approximately 
        {(stats['total_carbon'] / 10000):.2f} cars annually. Additionally, these trees 
        produce {stats['total_oxygen']:.2f} kg of oxygen per year, contributing significantly 
        to air quality improvement and ecosystem health.
        """
        story.append(Paragraph(carbon_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Carbon by species
        carbon_data = self.analyzer.get_carbon_by_species()
        top_carbon = sorted(carbon_data.items(), key=lambda x: x[1], reverse=True)[:5]
        
        carbon_table_data = [['Species', 'Carbon Sequestration (kg CO₂/year)']]
        for species, carbon in top_carbon:
            carbon_table_data.append([species, f"{carbon:.2f}"])
        
        carbon_table = Table(carbon_table_data, colWidths=[3*inch, 2*inch])
        carbon_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(Paragraph("Top Carbon Sequestration by Species", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        story.append(carbon_table)
        story.append(PageBreak())
        
        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))
        
        recommendations = f"""
        Based on the analysis of {stats['total_trees']} trees across {stats['total_locations']} locations:
        <br/><br/>
        1. <b>Species Diversity:</b> Continue planting diverse species to ensure ecosystem resilience.
        The current diversity of {stats['total_species']} species is {
            'excellent' if stats['total_species'] > 10 else 
            'good' if stats['total_species'] > 5 else 'needs improvement'
        }.<br/><br/>
        2. <b>Carbon Champions:</b> Consider planting more {stats['most_carbon_efficient']} trees, 
        as they show the highest carbon sequestration rates.<br/><br/>
        3. <b>Maintenance:</b> Regular monitoring and care of existing trees will maximize their 
        environmental benefits.<br/><br/>
        4. <b>Expansion:</b> Based on current carbon sequestration rates, planting 
        {int(stats['total_trees'] * 0.2)} more trees could increase annual CO₂ absorption by 
        {stats['total_carbon'] * 0.2:.2f} kg.
        """
        
        story.append(Paragraph(recommendations, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = """
        <para align=center>
        <font size=10 color='#7f8c8d'>
        Generated by ArborTag © 2024 NatureMarkSystems LLP<br/>
        For more information, visit www.naturemarksystems.com
        </font>
        </para>
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer