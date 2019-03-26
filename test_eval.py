# -*- coding: utf-8 -*-

"""
Some unit test for the evaluate_result_reg and evaluate_result_str of the eval 
class from eval.py

Usage: 
pytest test_eval.py
    or
python -mpytest test_eval.py

(you need to add pytest to your Python installation)

JL Meunier - March 2019
Naver Labs Europe
"""
import xml.dom.minidom

from eval import eval
from data_structure import ResultStructure


# ---  Utilities  -------------------------------------------------------
def OkErrMiss(o):
    """
    compute Ok, errors, missed from the ResultStructure object
    return a triple (ok, err, miss)
    """
    ok = o.truePos
    err = o.resTotal - ok
    miss = o.gtTotal - ok
    return ok, err, miss

def _regEval(gt_dom, result_dom, iou_value):
    """
    encapsulate the evaluate_result_reg to return ok, err, miss
    """
    o = eval.evaluate_result_reg(gt_dom, result_dom, iou_value)
    # print(o)
    return OkErrMiss(o)
    
def _rectangle(w, h, x0=0, y0=0, bClosed=True):
    """
    create a rectangle with bottom left corner at 0,0 or at x,y if given
    
    the list of coordinates is closed (start==end) if bClosed is True
    return the corresponding DOM
    """
    
    assert w > 0
    assert h > 0
        
    sXml = """<?xml version="1.0" encoding="UTF-8"?>
<document filename="table1.jpg">
    %s
</document>
""" % _table(x0, y0, w, h, bClosed)
    return xml.dom.minidom.parseString(sXml)

def _multi_rectangle(lxywh):
    """
    return a DOM containing multiple tables
    """
    sXmlTable = ""
    for x,y,w,h in lxywh:
        assert w > 0 and h > 0
        sXmlTable += "\n%s" % _table(x, y, w, h, False)
        
    sXml = """<?xml version="1.0" encoding="UTF-8"?>
<document filename="table1.jpg">
    %s
</document>
""" % sXmlTable

    return xml.dom.minidom.parseString(sXml)    

def _table(x, y, w, h, bClosed=True):
    """
    XML Table element as a string
    """
    if bClosed:
        #close the list of coordinates
        sPoints = "%d,%d %d,%d %d,%d %d,%d %d,%d" % (x,y , x+w,y , x+w,y+h , x,y+h , x,y)
    else:
        sPoints = "%d,%d %d,%d %d,%d %d,%d"       % (x,y , x+w,y , x+w,y+h , x,y+h)
    
    sXml = """
    <table>
        <Coords points="%s"/>
    </table>
    """ % (sPoints)
    return sXml

# -----------------------------------------------------------------------
def test_reg_simple():
    """
    a square compared to itself
    """
    for bClosedCoords in [True, False]:
        for IoU in [0.1, 0.5, 0.9, 1.0]:
            assert _regEval( _rectangle(100, 100, bClosed=bClosedCoords)
                           , _rectangle(100, 100)
                           , 0.9) == (1, 0, 0)
        
        GT = _rectangle(100, 100, bClosed=bClosedCoords)
        assert _regEval( GT, _rectangle(89, 100)
                        , 0.89) == (1, 0, 0)
        assert _regEval( GT, _rectangle(89, 100)
                        , 0.9) == (0, 1, 1)
        assert _regEval( GT, _rectangle(90, 100)
                        , 0.9) == (1, 0, 0)
        assert _regEval( GT, _rectangle(91, 100)
                        , 0.9) == (1, 0, 0)
        
        assert _regEval( GT, _rectangle(100, 89)
                        , 0.9) == (0, 1, 1)
        assert _regEval( GT, _rectangle(100, 90)
                        , 0.9) == (1, 0, 0)
        assert _regEval( GT, _rectangle(100, 91)  
                        , 0.9) == (1, 0, 0)


def test_reg_quarter():
    """
    a square compared to its quarter
    """
    GT = _rectangle(100, 100)
    assert _regEval( GT, _rectangle(50, 50)  
                    , 0.9) == (0, 1, 1)
    assert _regEval( GT, _rectangle(50, 50)  
                    , 0.24) == (1, 0, 0)
    assert _regEval( GT, _rectangle(50, 50)  
                    , 0.25) == (1, 0, 0)


    GT = _rectangle(100, 100, x0=50, y0=50)
    assert _regEval( GT, _rectangle(100, 100)  
                    , 0.9) == (0, 1, 1)
    iou = 50*50 / (7 * 50*50)
    print("expected=", iou)
    assert _regEval( GT, _rectangle(100, 100) 
                    , iou + 0.01) == (0, 1, 1)
    assert _regEval( GT, _rectangle(100, 100) 
                    , iou - 0.01) == (1, 0, 0)
   
    
def test_multi_table():
    """
    what if we have several tables on a page?
    """
    
    GT = _multi_rectangle([(0 ,0 ,100, 100)
                           , (200, 200, 100, 300)])
    assert _regEval( GT, GT  
                    , 1.0) == (2, 0, 0)     
    assert _regEval( GT, GT  
                    , 0.1) == (2, 0, 0)   
    
    # one missing table
    RUN =_multi_rectangle([(0 ,0 ,100, 100)
                           ])
    assert _regEval( GT, RUN  
                    , 1.0) == (1, 0, 1)     
    assert _regEval( GT, RUN  
                    , 0.1) == (1, 0, 1)   
    
    # one extra table
    RUN =_multi_rectangle([(0 ,0 ,100, 100)
                           , (200, 200, 100, 300)
                           , (1000 ,1000 ,1100, 1100)
                           ])
    assert _regEval( GT, RUN  
                    , 1.0) == (2, 1, 0)     
    assert _regEval( GT, RUN  
                    , 0.1) == (2, 1, 0)   
    
    # messy situation with one predicted table in middle overlapping the two GT tables
    # but the 2nd one is "more" overlapped
    RUN =_multi_rectangle([(50 , 50 , 300, 350)
                           ])
    res = _regEval( GT, RUN, 1.0)
    assert res == (0, 1, 2), res
    res = _regEval( GT, RUN, 0.01)
    assert res == (1, 0, 1), res
    
    iou1 = 50*50 / (100*100+300*350-50*50)  # overlap with 1st GT table 
    iou2 = 200*100 / (100*300+300*350-200*100)  # overlap with 2nd GT table 

    # 1st and middle on one in RUN
    RUN =_multi_rectangle([(0 ,0 ,100, 100)
                           , (50 , 50 , 300, 350)
                           ])
    res = _regEval( GT, RUN, 1.0)
    assert res == (1, 1, 1), res
    res = _regEval( GT, RUN, 0.01)
    assert res == (2, 0, 0), res
    res = _regEval( GT, RUN, iou2-0.01)
    assert res == (2, 0, 0), res
    res = _regEval( GT, RUN, iou2+0.01)
    assert res == (1, 1, 1), res

    
    # 2nd and middle on one in RUN
    RUN =_multi_rectangle([(200, 200, 100, 300)
                           , (50 , 50 , 300, 350)
                           ])
    res = _regEval( GT, RUN, 1.0)
    assert res == (1, 1, 1), res
    res = _regEval( GT, RUN, 0.01)
    assert res == (2, 0, 0), res
    res = _regEval( GT, RUN, iou2-0.01)
    assert res == (1, 1, 1), res
    res = _regEval( GT, RUN, iou2+0.01)
    assert res == (1, 1, 1), res  
    # middle one should match the 1st one  
    res = _regEval( GT, RUN, iou1-0.01)
    assert res == (2, 0, 0), res
    res = _regEval( GT, RUN, iou1+0.01)
    assert res == (1, 1, 1), res

    # 1st and 2nd and middle one
    RUN =_multi_rectangle([(0 ,0 ,100, 100)
                           , (200, 200, 100, 300)
                           , (50 , 50 , 300, 350)
                           ])
    res = _regEval( GT, RUN, 1.0)
    assert res == (2, 1, 0), res
    res = _regEval( GT, RUN, 0.01)
    assert res == (2, 1, 0), res
    res = _regEval( GT, RUN, iou2-0.01)
    assert res == (2, 1, 0), res
    res = _regEval( GT, RUN, iou2+0.01)
    assert res == (2, 1, 0), res  
    # middle one should match the 1st one  
    res = _regEval( GT, RUN, iou1-0.01)
    assert res == (2, 1, 0), res
    res = _regEval( GT, RUN, iou1+0.01)
    assert res == (2, 1, 0), res

if __name__ == "__main__":
    # to test manually some code...
    # test_reg_quarter()
    test_multi_table()
    
    
    
    
    