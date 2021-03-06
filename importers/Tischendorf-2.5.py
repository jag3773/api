#!/usr/bin/env python
# encoding: utf-8

work1_id = 1 # Tischendorf Kethiv
work1_variant_bit = 0b00000001
work2_id = 2 # Tischendorf Qere
work2_variant_bit = 0b00000010

import sys, string, os, re, unicodedata, urllib, zipfile, StringIO, datetime
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../')) #There's probably a better way of doing this
from openscriptures import settings
setup_environ(settings)
from openscriptures.api.models import *
from openscriptures.api.importers import import_helpers
from openscriptures.api import osis

# Abort if MS has already been added (or --force not supplied)
import_helpers.abort_if_imported(work1_id)

# Download the source file
source_url = "http://files.morphgnt.org/tischendorf/Tischendorf-2.5.zip"
import_helpers.download_resource(source_url)

# Delete existing works
import_helpers.delete_work(work2_id)
import_helpers.delete_work(work1_id)

#TODO: Get better title?
#TODO: source_url should be base

# Work for Kethiv edition (base text for qere)
work1 = Work(
    id           = work1_id,
    title        = "Tischendorf 8th ed. v2.5",
    language     = Language('grc'),
    type         = 'Bible',
    osis_slug    = 'Tischendorf',
    publish_date = datetime.date(2009, 5, 29),
    import_date  = datetime.datetime.now(),
    variant_bit  = work1_variant_bit,
    creator      = "<a href='http://en.wikipedia.org/wiki/Constantin_von_Tischendorf' title='Constantin von Tischendorf @ Wikipedia'>Constantin von Tischendorf</a>. Based on G. Clint Yale's Tischendorf text and on Dr. Maurice A. Robinson's Public Domain Westcott-Hort text. Edited by <a href='http://www.hum.aau.dk/~ulrikp/'>Ulrik Sandborg-Petersen</a>.",
    source_url   = source_url,
    license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
)
work1.save()
WorkServer.objects.create(
    work = work1,
    server = Server.objects.get(is_self = True)
)


#TODO: Do we even need another separate work?

# Work for Qere edition (Kethiv is base text)
import_helpers.delete_work(work2_id)
work2 = Work(
    id           = work2_id,
    title        = "Tischendorf 8th ed. v2.5 (Corrected)",
    language     = Language('grc'),
    type         = 'Bible',
    osis_slug    = 'Tischendorf-corrected',
    publish_date = datetime.date(2009, 5, 29),
    import_date  = datetime.datetime.now(),
    variant_bit  = work2_variant_bit,
    variants_for_work = work1,
    creator      = "<a href='http://en.wikipedia.org/wiki/Constantin_von_Tischendorf' title='Constantin von Tischendorf @ Wikipedia'>Constantin von Tischendorf</a>. Based on G. Clint Yale's Tischendorf text and on Dr. Maurice A. Robinson's Public Domain Westcott-Hort text. Edited by <a href='http://www.hum.aau.dk/~ulrikp/'>Ulrik Sandborg-Petersen</a>.",
    source_url   = source_url,
    license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
)
work2.save()
WorkServer.objects.create(
    work = work2,
    server = Server.objects.get(is_self = True)
)


bookFilenameLookup = {
	'Matt'   : "MT.txt"   ,
	'Mark'   : "MR.txt"   ,
	'Luke'   : "LU.txt"   ,
	'John'   : "JOH.txt"  ,
	'Acts'   : "AC.txt"   ,
	'Rom'    : "RO.txt"   ,
	'1Cor'   : "1CO.txt"  ,
	'2Cor'   : "2CO.txt"  ,
	'Gal'    : "GA.txt"   ,
	'Eph'    : "EPH.txt"  ,
	'Phil'   : "PHP.txt"  ,
	'Col'    : "COL.txt"  ,
	'1Thess' : "1TH.txt"  ,
	'2Thess' : "2TH.txt"  ,
	'1Tim'   : "1TI.txt"  ,
	'2Tim'   : "2TI.txt"  ,
	'Titus'  : "TIT.txt"  ,
	'Phlm'   : "PHM.txt"  ,
	'Heb'    : "HEB.txt"  ,
	'Jas'    : "JAS.txt"  ,
	'1Pet'   : "1PE.txt"  ,
	'2Pet'   : "2PE.txt"  ,
	'1John'  : "1JO.txt"  ,
	'2John'  : "2JO.txt"  ,
	'3John'  : "3JO.txt"  ,
	'Jude'   : "JUDE.txt" ,
	'Rev'    : "RE.txt"   ,   
}

#NOTICE: We need to do the same thing with Tischendorf that we did with TNT: there is a corrected edition
# - One word per line
# - Space-separated fields (except for the last two)
# - - fields:
#   0. Book (corresponds to the filename, which is the Online Bible standard)
#   1. Chapter:Verse.word-within-verse
#   2. Pagraph break ("P") / Chapter break ("C") / No break (".") (see
#      below)
#   3. The text as it is written in the printed Tischendorf (Kethiv)
#   4. The text as the editor thinks it should have been (Qere)
#   5. The morphological tag (following the Qere)
#   6. The Strong's number (following the Qere)
#   7. The lemma in two versions:
#     7.a The first version, which corresponds to The NEW Strong's
#       Complete Dictionary of Bible Words.
#     7.b Followed by the string " ! "
#     7.c Then the second version, which corresponds to Friberg, Friberg
#       and Miller's ANLEX.
#     There may be several words in each lemma.
# 
# All Strong's numbers are single numbers with 1,2,3, or 4 digits.
# 
# The third column (designated "2." above) has precisely one of three
# values:
# 
# - "." : No break occurs
# - "P" : A paragraph break occurs
# - "C" : A chapter break occurs
# 
# Most paragraph breaks occur on a verse boundary, but not all paragraph
# breaks do.
# 
# A program counting the "C"s can rely on them to count the chapters,
# i.e., even if a chapter break occurs in a verse which belongs to
# chapter X, that means that Tischendorf thought that that verse belongs
# to chapter X+1.  This occurs, for example, in Revelation 12:18, where
# the chapter break occurs in chapter 12, meaning that verse 12:18 needs
# to be shown with chapter 13.


#puncchrs = re.escape(''.join(unichr(x) for x in range(65536) if unicodedata.category(unichr(x)) == 'Po'))
puncchrs = re.escape(ur'.·,;:!?"\'')
lineParser = re.compile(ur"""^
        (?P<book>\S+)\s+            # Book (corresponds to the filename, which is the Online Bible standard)
        (?P<chapter>\d+):           # Chapter
        (?P<verse>\d+)\.            # Verse
        (?P<position>\d+)\s+        # word-within-verse
        (?P<break>\S)\s+            # Pagraph break ("P") / Chapter break ("C") / No break (".")
        (?P<kethivStartBracket>\[)?
        (?P<kethiv>\S+?)            # The text as it is written in the printed Tischendorf (Kethiv)
        (?P<kethivPunc>[%s])?       # Kethiv punctuation
        (?P<kethivEndBracket>\])?\s+
    (?P<rawParsing>
        (?P<qereStartBracket>\[)?
        (?P<qere>\S+?)              # The text as the editor thinks it should have been (Qere)
        (?P<qerePunc>  [%s])?       # Qere punctuation
        (?P<qereEndBracket>\])?\s+
        (?P<morph>\S+)\s+           # The morphological tag (following the Qere)
        (?P<strongsNumber>\d+)\s+   # The Strong's number (following the Qere)
        (?P<strongsLemma>.+?)       # Lemma which corresponds to The NEW Strong's Complete Dictionary of Bible Words. (There may be several words in each lemma.)
        \s+!\s+                     # A " ! " separates the lemmas
        (?P<anlexLemma>.+?)         # Lemma which corresponds to Friberg, Friberg and Miller's ANLEX. (There may be several words in each lemma.)
    )
    \s*$""" % (puncchrs, puncchrs),
    re.VERBOSE
)



# Get the subset of OSIS book codes provided on command line
limited_book_codes = []
#limited_osis_ids = []
for arg in sys.argv:
    id_parts = arg.split(".")
    if id_parts[0] in osis.BOOK_ORDERS["Bible"]["KJV"]:
        limited_book_codes.append(id_parts[0])
        #limited_osis_ids.append(arg)

# I cannot believe Python doesn't have this built in
#def grep(regexp,list):
#    "Grep from http://casa.colorado.edu/~ginsbura/pygrep.htm"
#    expr = re.compile(regexp)
#    results = []
#    for text in list:
#        match = expr.search(text)
#        if match != None:
#            results.append(match.string)
#    return results


if len(limited_book_codes):
    book_codes = limited_book_codes
else:
    book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]


#book_codes = import_helpers.get_book_code_args()
#if len(book_codes) == 0:
#    book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]

# Read each of the Book files
structCount = 1
tokenCount = 1
zip = zipfile.ZipFile(os.path.basename(source_url))
for book_code in book_codes:
    if not bookFilenameLookup.has_key(book_code):
        continue
    
    print "Book:", osis.BOOK_NAMES["Bible"][book_code]
    
    # Set up the book ref
    structs = {}
    structs[Structure.BOOK] = Structure(
        work = work1,
        type = Structure.BOOK,
        osis_id = book_code,
        position = structCount,
        numerical_start = book_codes.index(book_code),
        variant_bits = work2_variant_bit | work1_variant_bit,
        source_url = "zip:" + source_url + "!/Tischendorf-2.5/Unicode/" + bookFilenameLookup[book_code]
        #title = osis.BOOK_NAMES["Bible"][book_code]
    )
    structCount += 1
    
    bookTokens = []
    
    current_chapter = None
    current_verse = None
    
    def closeStructure(type):
        if structs.has_key(type):
            assert(structs[type].start_token is not None)
            if structs[type].end_token is None:
                structs[type].end_token = bookTokens[-1]
            structs[type].save()
            del structs[type]
    
    lineNumber = -1
    for line in StringIO.StringIO(zip.read("Tischendorf-2.5/Unicode/" + bookFilenameLookup[book_code])):
        lineNumber += 1
        lineMatches = lineParser.match(unicodedata.normalize("NFC", unicode(line, 'utf-8')))
        if lineMatches is None:
            print " -- Warning: Unable to parse line: " + line 
            continue
        
        # Skip verses we're not importing right now
        #verse_osisid = book_code + "." + lineMatches.group('chapter') + "." + lineMatches.group('verse')
        #if len(limited_osis_ids) and len(grep(verse_osisid, limited_osis_ids)) != 0:
        #    continue
        
        # New Chapter start
        if lineMatches.group('chapter') != current_chapter:
            # End the previous chapter
            closeStructure(Structure.CHAPTER)
            
            # Start the next chapter
            current_chapter = lineMatches.group('chapter')
            structs[Structure.CHAPTER] = Structure(
                work = work1, # remember work2 is subsumed by work1
                type = Structure.CHAPTER,
                position = structCount,
                osis_id = book_code + "." + current_chapter,
                numerical_start = current_chapter,
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            print structs[Structure.CHAPTER].osis_id
            structCount += 1
        
        # New Verse start
        if lineMatches.group('verse') != current_verse:
            # End the previous verse
            closeStructure(Structure.VERSE)
            
            # Start the next verse
            current_verse = lineMatches.group('verse')
            structs[Structure.VERSE] = Structure(
                work = work1, # remember work2 is subsumed by work1
                type = Structure.VERSE,
                position = structCount,
                osis_id = book_code + "." + current_chapter + "." + current_verse,
                numerical_start = current_verse,
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            print structs[Structure.VERSE].osis_id
            structCount += 1
        
        
        # End paragraph
        paragraph_marker = None
        if lineMatches.group('break') == 'P' and structs.has_key(Structure.PARAGRAPH):
            assert(len(bookTokens) > 0)
            
            paragraph_marker = Token(
                data     = u"\u2029", #¶ "\n\n"
                type     = Token.WHITESPACE, #i.e. PARAGRAPH
                work     = work1,
                position = tokenCount,
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            tokenCount += 1
            paragraph_marker.save()
            structs[Structure.PARAGRAPH].end_marker = paragraph_marker
            closeStructure(Structure.PARAGRAPH)
            bookTokens.append(paragraph_marker)
        
        # Start paragraph
        if len(bookTokens) == 0 or lineMatches.group('break') == 'P':
            assert(not structs.has_key(Structure.PARAGRAPH))
            print "¶"
            structs[Structure.PARAGRAPH] = Structure(
                work = work1, # remember work2 is subsumed by work1
                type = Structure.PARAGRAPH,
                position = structCount,
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            if paragraph_marker:
                structs[Structure.PARAGRAPH].start_marker = paragraph_marker
            structCount += 1
        
        # Insert whitespace
        if not paragraph_marker and len(bookTokens) > 0:
            ws_token = Token(
                data     = " ",
                type     = Token.WHITESPACE,
                work     = work1,
                position = tokenCount,
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            tokenCount += 1
            ws_token.save()
            bookTokens.append(ws_token)
        
        assert(lineMatches.group('kethivPunc') == lineMatches.group('qerePunc'))
        assert(lineMatches.group('kethivStartBracket') == lineMatches.group('qereStartBracket'))
        assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))
        
        #if string.find(line, '[') != -1 or string.find(line, ']') != -1 or lineMatches.group('kethiv') != lineMatches.group('qere'):
        #    print line
        #continue
        
        lineTokens = []
        
        
        # Open UNCERTAIN1 bracket
        assert(lineMatches.group('kethivStartBracket') == lineMatches.group('qereStartBracket'))
        if lineMatches.group('kethivStartBracket'):
            assert(not structs.has_key(Structure.UNCERTAIN1))
            print "### OPEN BRACKET"
            
            # Make start_marker for UNCERTAIN1
            open_bracket_token = Token(
                data     = '[',
                type     = Token.PUNCTUATION,
                work     = work1,
                position = tokenCount
            )
            tokenCount += 1
            open_bracket_token.save()
            lineTokens.append(open_bracket_token)
            
            # Create the UNCERTAIN1 structure
            structs[Structure.UNCERTAIN1] = Structure(
                work = work1, # remember work2 is subsumed by work1
                type = Structure.UNCERTAIN1,
                position = structCount,
                variant_bits = work2_variant_bit | work1_variant_bit,
                start_marker = open_bracket_token
            )
            structCount += 1
        
        # Kethiv token
        token_work1 = Token(
            data     = lineMatches.group('kethiv'),
            type     = Token.WORD,
            work     = work1,
            position = tokenCount,
            variant_bits = work1_variant_bit | work2_variant_bit,
            relative_source_url = "#line(%d)" % lineNumber
        )
        if lineMatches.group('kethiv') == lineMatches.group('qere'):
            token_work1.variant_bits = work1_variant_bit | work2_variant_bit
        else:
            token_work1.variant_bits = work1_variant_bit
        tokenCount += 1
        token_work1.save()
        lineTokens.append(token_work1)
        
        # Make this token the start of the UNCERTAIN structure
        if lineMatches.group('kethivStartBracket'):
            structs[Structure.UNCERTAIN1].start_token = token_work1
        
        # Qere token
        if lineMatches.group('kethiv') != lineMatches.group('qere'):
            print lineMatches.group('kethiv') + " != " + lineMatches.group('qere')
            token_work2 = Token(
                data     = lineMatches.group('qere'),
                type     = Token.WORD,
                work     = work1, # yes, this should be work1
                position = tokenCount,   #token_work1.position #should this be the same!?
                variant_bits = work2_variant_bit,
                relative_source_url = "#line(%d)" % lineNumber
                # What will happen with range?? end_token = work1, but then work2?
                # Having two tokens at the same position could mean that they are
                #  co-variants at that one spot. But then we can't reliably get
                #  tokens by a range? Also, the position can indicate transposition?
            )
            tokenCount += 1
            token_work2.save()
            lineTokens.append(token_work2)
        
        # Punctuation token
        assert(lineMatches.group('kethivPunc') == lineMatches.group('qerePunc'))
        if lineMatches.group('kethivPunc'):
            punc_token = Token(
                data     = lineMatches.group('kethivPunc'),
                type     = Token.PUNCTUATION,
                work     = work1,
                position = tokenCount,
                variant_bits = work1_variant_bit | work2_variant_bit
            )
            tokenCount += 1
            punc_token.save()
            lineTokens.append(punc_token)
        
        # Close UNCERTAIN1 bracket
        assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))
        if lineMatches.group('kethivEndBracket'):
            assert(structs.has_key(Structure.UNCERTAIN1))
            print "### CLOSE BRACKET"
            
            structs[Structure.UNCERTAIN1].end_token = lineTokens[-1]
            
            # Make end_marker for UNCERTAIN1
            close_bracket_token = Token(
                data     = ']',
                type     = Token.PUNCTUATION,
                work     = work1,
                position = tokenCount,
                variant_bits = work1_variant_bit | work2_variant_bit
            )
            tokenCount += 1
            close_bracket_token.save()
            
            # Close the UNCERTAIN1 structure
            structs[Structure.UNCERTAIN1].end_marker = close_bracket_token
            closeStructure(Structure.UNCERTAIN1)
            lineTokens.append(open_bracket_token)
        
        
        # Set the start_token for each structure that isn't set
        for struct in structs.values():
            if struct.start_token is None:
                struct.start_token = lineTokens[0]
        
        for token in lineTokens:
            bookTokens.append(token)
    
    for structType in structs.keys():
        closeStructure(structType)

print "structCount: " + str(structCount)
print "tokenCount:  " + str(tokenCount)
    
