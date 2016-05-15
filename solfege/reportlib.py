# GNU Solfege - free ear training software
# Copyright (C) 2007, 2008, 2011 Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import codecs


class Heading(object):

    def __init__(self, level, text):
        """
        1 is top level heading, 2 is below that.
        """
        self.m_level = level
        self.m_text = text


class Report(list):
    pass


class Paragraph(str):
    pass


class Table(list):

    def append_row(self, *cells):
        self.append(cells)


class TableRow(list):
    pass


class ReportWriterCommon(object):

    def __init__(self, report, filename):
        self.m_outfile = codecs.open(filename, "w", "utf-8")
        self.write_report(report)
        self.m_outfile.close()


class HtmlReport(ReportWriterCommon):

    def write_report(self, report):
        print("""<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style type="text/css">
th { text-align: left; border-bottom: 1px solid black}
</style>
</head>
<body>""", file=self.m_outfile)
        for elem in report:
            f = {'Heading': self.write_heading,
                 'Paragraph': self.write_paragraph,
                 'Table': self.write_table,
                }[elem.__class__.__name__](elem)
        print("</body>\n</html>", file=self.m_outfile)

    def write_heading(self, heading):
        print("<h%(level)i>%(str)s</h%(level)i>" % {
            'level': heading.m_level,
            'str': heading.m_text}, file=self.m_outfile)

    def write_paragraph(self, paragraph):
        print("<p>%s</p>" % paragraph, file=self.m_outfile)

    def write_table(self, table):
        print("<table border='0'>", file=self.m_outfile)
        for row in table:
            self.write_tablerow(row)
        print("</table>", file=self.m_outfile)

    def write_tablerow(self, row):
        print("<tr>", file=self.m_outfile)
        for t in row:
            print("<td>%s</td>" % t, file=self.m_outfile)
        print("</tr>", file=self.m_outfile)


class LatexReport(ReportWriterCommon):

    def write_report(self, report):
        print(r"\documentclass{article}", file=self.m_outfile)
        print(r"\begin{document}", file=self.m_outfile)
        for elem in report:
            f = {'Heading': self.write_heading,
                 'Paragraph': self.write_paragraph,
                 'Table': self.write_table,
            }[elem.__class__.__name__](elem)
        print(r"\end{document}", file=self.m_outfile)

    def write_heading(self, heading):
        print(r"\section{%s}" % heading.m_text, file=self.m_outfile)

    def write_paragraph(self, paragraph):
        print(paragraph, file=self.m_outfile)

    def write_table(self, t):
        pass

    def write_tablerow(self, t):
        pass
