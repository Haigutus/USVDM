<?xml version="1.0" encoding="UTF-8" ?>
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                xmlns:md="http://iec.ch/TC57/61970-552/ModelDescription/1#"
                xmlns:dct="http://purl.org/dc/terms/#"
                xmlns:dcat="http://www.w3.org/ns/dcat#"
                xmlns:time="http://www.w3.org/2006/time#"
                xmlns:eumd="http://entsoe.eu/ns/Metadata-European#"
                xmlns:owl="http://www.w3.org/2002/07/owl#"
                xmlns:prov="http://www.w3.org/ns/prov#"
                xmlns:sh="http://www.w3.org/ns/shacl#"
                xmlns="http://entsoe.eu/checks" version="1.0">
    <xsl:output method="xml" omit-xml-declaration="no" encoding="UTF-8" indent="yes" />
    <xsl:template match="sh:ValidationReport">

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
                <xsl:value-of select="sh:conforms"/>
            </xsl:element>

            <!-- we need the full extended header in the reporing format -->

            <xsl:element name = "SingleProfile">
                        <xsl:attribute name="created">
                            <xsl:value-of select="prov:generatedAtTime"/>
                        </xsl:attribute>
                        <xsl:attribute name="processType">
                            <xsl:value-of select="substring-after(dct:accrualPeriodicity/@rdf:resource, '#')"/>
                        </xsl:attribute>
                        <xsl:attribute name="profile">
                            <xsl:value-of select="substring-after(dcat:keyword, '#')"/>
                        </xsl:attribute>
                        <xsl:attribute name="qualityIndicator">
                            <xsl:text>Processible</xsl:text> <!-- TODO: put if here, linked to sh:conforms -->
                        </xsl:attribute>
                        <xsl:attribute name="resource">
                            <xsl:value-of select="dct:identifier"/>
                        </xsl:attribute>
                        <xsl:attribute name="scenarioTime">
                            <xsl:value-of select="md:Model.scenarioTime"/>
                        </xsl:attribute>
                        <!-- Not actually tso, but the region, this comes clear in case of Energinet -->
                        <xsl:attribute name="tso">
                            <xsl:value-of select="prov:atLocation/@rdf:resource"/> <!-- TODO: see if we add TSO/AREA names or we can swich to EIC on QAS side -->
                        </xsl:attribute>
                        <xsl:attribute name="version">
                             <xsl:value-of select="md:Model.version"/>
                        </xsl:attribute>

                        <!--REFERENCES USED IN CASE OF IGM OBJECT-->
                        <xsl:for-each select = "MetaData/DependantOn">
                            <xsl:element name = "resource">
                                <xsl:value-of select="modelid"/>
                            </xsl:element>
                        </xsl:for-each>

                        <!--ERRORS-->

            </xsl:element>

            <xsl:for-each select="sh:result">

                <xsl:element name = "RuleViolation">
                    <xsl:attribute name="validationLevel">
                        <xsl:value-of select="sh:ValidationResult/validationLevel/@rdf:resource"/> <!-- TODO: Validation levels need to be added -->
                    </xsl:attribute>
                    <xsl:attribute name="ruleId">
                        <xsl:value-of select="substring-after(sh:ValidationResult/sh:sourceConstraintComponent/@rdf:resource, '#')"/>
                    </xsl:attribute>
                    <xsl:attribute name="severity">
                        <xsl:value-of select="sh:ValidationResult/sh:resultSeverity/@rdf:resource"/> <!-- TODO: Map to used severity levels on QAS portal from SHACL -->
                    </xsl:attribute>
                    <xsl:element name = "Message">
                        <xsl:value-of select="sh:ValidationResult/sh:resultMessage"/>
                    </xsl:element>
                </xsl:element>


            </xsl:for-each>

        </xsl:element>

    </xsl:template>
</xsl:transform>

