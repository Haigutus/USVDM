<?xml version="1.0" encoding="UTF-8" ?>
<!--
MIT License

Copyright (c) 2021 Kristjan Vilgo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                xmlns:md="http://iec.ch/TC57/61970-552/ModelDescription/1#"
                xmlns:dct="http://purl.org/dc/terms/#"
                xmlns:dcat="http://www.w3.org/ns/dcat#"
                xmlns:time="http://www.w3.org/2006/time#"
                xmlns:eumd="http://entsoe.eu/ns/Metadata-European#"
                xmlns:owl="http://www.w3.org/2002/07/owl#"
                xmlns:prov="http://www.w3.org/ns/prov#"
                xmlns:cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#"
                xmlns:sh="http://www.w3.org/ns/shacl#"
                xmlns="http://entsoe.eu/checks" version="1.0">
    <xsl:output method="xml" omit-xml-declaration="no" encoding="UTF-8" indent="yes" />
    <xsl:template match="rdf:RDF">

    <!--ROOT ELEMENT-->
        <xsl:element name = "QAReport">
            <xsl:attribute name="created" select="current-dateTime()"/>
            <xsl:attribute name="schemeVersion">
                <xsl:text>2.0</xsl:text>
            </xsl:attribute>
            <xsl:attribute name="serviceProvider">
                <xsl:text>Local</xsl:text>
            </xsl:attribute>
            <xsl:element name = "processible">
                <xsl:value-of select="sh:ValidationReport/sh:conforms"/>
            </xsl:element>

            <!-- we need the full extended header in the reporing format -->

            <xsl:element name = "SingleProfile">
                        <xsl:attribute name="created">
                            <xsl:value-of select="md:FullModel/md:Model.created"/>
                        </xsl:attribute>
                        <xsl:attribute name="processType">
                            <xsl:value-of select="md:FullModel/cgmbp:Model.businessProcess"/>
                        </xsl:attribute>
                        <xsl:attribute name="profile">
                            <xsl:value-of select="md:FullModel/cgmbp:Model.modelPart"/>
                        </xsl:attribute>
                        <xsl:attribute name="qualityIndicator">
                            <xsl:text>Processible</xsl:text> <!-- TODO: put if here, linked to sh:conforms -->
                        </xsl:attribute>
                        <xsl:attribute name="resource">
                            <xsl:value-of select="md:FullModel/@rdf:about"/>
                        </xsl:attribute>
                        <xsl:attribute name="scenarioTime">
                            <xsl:value-of select="md:FullModel/md:Model.scenarioTime"/>
                        </xsl:attribute>
                        <!-- Not actually tso, but the region, this comes clear in case of Energinet -->
                        <xsl:attribute name="tso">
                            <xsl:value-of select="md:FullModel/cgmbp:Model.sourcingTSO"/> <!-- TODO: see if we add TSO/AREA names or we can swich to EIC on QAS side -->
                        </xsl:attribute>
                        <xsl:attribute name="version">
                             <xsl:value-of select="md:FullModel/md:Model.version"/>
                        </xsl:attribute>

                        <!--REFERENCES USED IN CASE OF IGM/CGM OBJECT
                        <xsl:for-each select = "MetaData/DependantOn">
                            <xsl:element name = "resource">
                                <xsl:value-of select="modelid"/>
                            </xsl:element>
                        </xsl:for-each>
                        -->

                        <!--ERRORS-->

            </xsl:element>

            <xsl:for-each select=".//sh:ValidationResult">

                <xsl:element name = "RuleViolation">
                    <xsl:attribute name="validationLevel">
                        <xsl:value-of select="substring-after(sh:propertyGroup/@rdf:resource, 'Level')"/> <!-- TODO: Validation levels need to be added -->
                    </xsl:attribute>
                    <xsl:attribute name="ruleId">
                        <xsl:value-of select="substring-after(sh:sourceShape/@rdf:resource, '#')"/>
                    </xsl:attribute>
                    <xsl:attribute name="severity">
                        <xsl:value-of select="substring-after(sh:resultSeverity/@rdf:resource, '#')"/> <!-- TODO: Map to used severity levels on QAS portal from SHACL -->
                    </xsl:attribute>
                    <xsl:element name = "Message">
                        <xsl:value-of select="concat(sh:resultMessage, ' VALUE:', sh:value, ' ID:', sh:focusNode/@rdf:resource)"/>
                    </xsl:element>
                </xsl:element>


            </xsl:for-each>

        </xsl:element>

    </xsl:template>
</xsl:transform>

