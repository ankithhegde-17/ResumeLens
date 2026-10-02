"""Server-to-server OCR transport. No keys/documents in URLs, browser or logs."""
import math
from urllib.parse import urlparse
import requests

ERROR = 'OCR is temporarily unavailable. Try again later or use a text-based PDF.'


def extract_remote(blob, filename, cfg):
    url=cfg.get('OCR_SERVICE_URL','').rstrip('/')
    secret=cfg.get('OCR_SERVICE_SECRET','')
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or len(secret)<32:
        raise ValueError('Image/scan processing needs the server OCR service configuration. Text-based PDFs still work.')
    try:
        with requests.Session() as transport:
            response=transport.post(url+'/extract',headers={'Authorization':'Bearer '+secret},
                files={'resume':(filename,blob,'application/octet-stream')},timeout=(5,35),allow_redirects=False)
        if not response.ok or len(response.content)>200000:
            raise ValueError(ERROR)
        result=response.json()
        pages=result.get('pages')
        expected='PDF' if filename.lower().endswith('.pdf') else 'Image'
        if result.get('source_type')!=expected or not isinstance(pages,list) or not 1<=len(pages)<=5:
            raise ValueError(ERROR)
        clean=[]
        for number,page in enumerate(pages,1):
            text=page.get('text'); confidence=page.get('confidence')
            if page.get('number')!=number or not isinstance(text,str) or len(text)>12000:
                raise ValueError(ERROR)
            if confidence is not None and (isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not math.isfinite(confidence) or not 0<=confidence<=1):
                raise ValueError(ERROR)
            engine=page.get('engine')
            if engine not in {'PDF text','RapidOCR'}: raise ValueError(ERROR)
            clean.append(dict(number=number,text=text,engine='Remote RapidOCR' if engine=='RapidOCR' else engine,confidence=confidence))
        if sum(len(p['text'].strip()) for p in clean)<40 or sum(len(p['text']) for p in clean)>35000: raise ValueError(ERROR)
        return dict(pages=clean,source_type=expected,notes=['Image/scan extraction used the private OCR service.'])
    except (requests.RequestException,ValueError,TypeError,AttributeError,KeyError):
        raise ValueError(ERROR) from None
