#!/usr/local/bin/python

# CGI for generating a web page that supports curators looking at the
# predicted reference section and validating whether the prediction is right.
# Curators enters pubmed ID and sees the results of the predicted reference
# removal.

import sys
#sys.path.insert(0, '/home/jsb/jax/prod/lib/python')
#sys.path.insert(0, '/usr/local/lib/python2.4')
#sys.path.insert(0, '/usr/local/mgi/lib/python')
sys.path.insert(0, '/home/jak/lib/python/mgi')
#import httpReader
import string
import cgi
import os
import db
import refSectionLib


def getParameters():
    form = cgi.FieldStorage()

    params = {}
    for k in form.keys():
	params[k] = form.getvalue(k)
    return params

def getReferenceInfo(pubmed):
    query = '''
    select a.accid pubmed, r.journal, r.title, bd.extractedtext
    from bib_refs r join bib_workflow_data bd on (r._refs_key = bd._refs_key)
	join acc_accession a on
	 (a._object_key = r._refs_key and a._logicaldb_key=29 -- pubmed
	  and a._mgitype_key=1 )
    where
    a.accid = '%s'
    ''' % str(pubmed)
    #--, translate(bd.extractedtext, E'\r', ' ') as "text" -- remove ^M's
    db.set_sqlServer  ('bhmgidevdb01')
    db.set_sqlDatabase('prod')
    db.set_sqlUser    ('mgd_public')
    db.set_sqlPassword('mgdpub')

    dbOutput = db.sql( string.split(query, '||'), 'auto')

    results = dbOutput[-1]	# list of results (should only be one)

    if len(results) == 0:
	return "Pubmed ID '%s' not found" % str(pubmed)
    else:
	return results[0]

def buildPage(params):
    head = """Content-type: text/html

	<HTML><HEAD><TITLE>Validate Ref Section</TITLE>
	<STYLE>
	table, th, td { border: 1px solid black; }
	.header { border: thin solid black; vertical-align: top; font-weight: bold }
	.value { border: thin solid black; vertical-align: top; }.highlight { background-color: yellow; }
	.right { text-align: right; }
	</STYLE>
	</HEAD>
	<BODY>
	<H3>Predicted Reference Section Validation</H3>
	"""
    paramReport = []
    if False:	# debugging
	paramReport = ['<p>Parameters']
	for i in params.items():
	    paramReport.append( '<br>%s: %s' % (i[0], i[1]) )
	paramReport.append('<br>End Parameters' )

    form = [
	    '<DIV CLASS="search">',
	    '<FORM ACTION="refsection.cgi" METHOD="GET">',
	    '<B>Pubmed ID </B>',
	    '<INPUT NAME="pubmed" TYPE="text" SIZE="25" autofocus>',
	    #'<INPUT NAME="isHidden" TYPE="hidden" VALUE="cannot see me">',
	    '<INPUT TYPE="submit" VALUE="Go">',
	    '</FORM>',
	    '</DIV>',
	    ]

    if params.has_key('pubmed'):
	refInfo = getReferenceInfo(params['pubmed'])
	if type(refInfo) == type(''):
	    refDisplay = refInfo
	else:
	    refDisplay = buildReferenceDetails(refInfo)
    else:
	refDisplay = ''

    body = '\n'.join(paramReport) + '\n'.join(form) + refDisplay

    tail = '</BODY></HTML>'
    print head + body + tail
    return

def buildReferenceDetails(refInfo):
    rsr = refSectionLib.RefSectionRemover()

    lastKeyWord, refStart = rsr.predictRefSection(refInfo['extractedtext'])
    lenText = len(refInfo['extractedtext'])
    lenRefs = lenText - refStart
    percent = 100 * float(lenRefs)/lenText

    pdfLink = '<a href="http://bhmgiei01.jax.org/usrlocalmgi/live/pdfviewer/pdfviewer.cgi?id=%s" target="_blank">PDF</a>' % refInfo['pubmed']
    body = [
	'<TABLE>',
	'<TR>',
	    '<TH>Link</TH>',
	    '<TH>Pubmed</TH>',
	    '<TH>Journal</TH>',
	    '<TH>Title</TH>',
	'</TR>',
	'<TR>',
	  '<TD> %s </TD>' % pdfLink,
	  '<TD> %s </TD>' % refInfo['pubmed'],
	  '<TD> %s </TD>' % refInfo['journal'],
	  '<TD> %s </TD>' % refInfo['title'],
	'</TR>',
	'</TABLE>',
	'<P>',
	'Doc length: %d &nbsp;&nbsp; Chars after: %d &nbsp;&nbsp; After: %4.1f%% &nbsp;&nbsp; Ref Section Matching Keyword: <B>%s</B>' % (lenText, lenRefs, percent, lastKeyWord),
	
	'<P>',
	'<TABLE>',
	'<TR>',
	    '<TH>Ref Section Removed</TH>'
	    '<TH>Original Text</TH>',
	'</TR>'
	'</TR>'
	    '<TD>',
		'<textarea rows="30" cols="70">',
		refInfo['extractedtext'][:refStart],
		'</textarea>',
	    '</TD>',
	    '<TD>',
		'<textarea rows="30" cols="70">',
		refInfo['extractedtext'],
		'</textarea>',
	    '</TD>',
	'</TR>'
	'</TABLE>',
    ]

    return '\n'.join(body)

buildPage(getParameters())
