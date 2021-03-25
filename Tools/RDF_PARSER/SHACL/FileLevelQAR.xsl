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

            <!-- MODEL HEADER / METADATA -->
            <xsl:element name = "SingleProfile">

                        <xsl:attribute name="created">
                            <xsl:value-of select="md:FullModel/md:Model.created"/>
                        </xsl:attribute>
                        <xsl:attribute name="resource">
                            <xsl:value-of select="md:FullModel/@rdf:about"/>
                        </xsl:attribute>
                        <xsl:attribute name="scenarioTime">
                            <xsl:value-of select="md:FullModel/md:Model.scenarioTime"/>
                        </xsl:attribute>
                        <xsl:attribute name="tso">                                        <!-- Not actually TSO, but the TSO area/region, this comes clear in case of Energinet -->
                            <xsl:value-of select="md:FullModel/cgmbp:Model.sourcingTSO"/> <!-- TODO: In future switch to EIC type Y (Area) here and on QAS side, then we can get rid of the mess of TSO/Area names not being aligned -->
                        </xsl:attribute>
                        <xsl:attribute name="version">
                             <xsl:value-of select="md:FullModel/md:Model.version"/>
                        </xsl:attribute>
                        <xsl:attribute name="processType">
                            <xsl:value-of select="md:FullModel/cgmbp:Model.businessProcess"/>
                        </xsl:attribute>
                        <xsl:attribute name="profile">
                            <xsl:value-of select="md:FullModel/cgmbp:Model.modelPart"/>
                        </xsl:attribute>
                        <xsl:attribute name="qualityIndicator">
                            <xsl:text>Processible</xsl:text>                              <!-- TODO: get list of allowed values and map to sh:conforms -->
                        </xsl:attribute>

            </xsl:element>

            <!-- ERRORS -->
            <xsl:for-each select=".//sh:ValidationResult">

                <xsl:element name = "RuleViolation">
                    <xsl:attribute name="validationLevel">
                        <xsl:value-of select="substring-after(sh:propertyGroup/@rdf:resource, 'Level')"/>
                    </xsl:attribute>
                    <xsl:attribute name="ruleId">
                        <xsl:value-of select="substring-after(sh:sourceShape/@rdf:resource, '#')"/>
                    </xsl:attribute>
                    <xsl:attribute name="severity">
                        <xsl:value-of select="substring-after(sh:resultSeverity/@rdf:resource, '#')"/>
                    </xsl:attribute>
                    <xsl:element name = "Message">
                        <xsl:value-of select="concat(sh:resultMessage, ' VALUE:', sh:value, ' ID:', sh:focusNode/@rdf:resource)"/>
                    </xsl:element>
                </xsl:element>

            </xsl:for-each>

            <!-- ADDITIONAL METADATA (needed for RSC-s) -->
            <xsl:if test="md:FullModel/cgmbp:Model.sourcingRSC != ''">
                <xsl:element name = "EMFInformation">
                    <xsl:attribute name="mergingEntity">
                        <xsl:value-of select="md:FullModel/cgmbp:Model.sourcingRSC"/>
                    </xsl:attribute>
                    <xsl:attribute name="cgmType">
                        <xsl:value-of select="md:FullModel/cgmbp:Model.cgmRegion"/>
                    </xsl:attribute>
                </xsl:element>
            </xsl:if>

        </xsl:element>

    </xsl:template>
</xsl:transform>