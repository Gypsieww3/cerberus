"""Confusion-matrix report for offline quality inspection data."""
def evaluate(y_true,y_pred):
    truth,pred=list(y_true),list(y_pred)
    if not truth or len(truth)!=len(pred) or any(type(v) is not bool for v in truth+pred):
        raise ValueError("Equal nonempty boolean label arrays required")
    tp=sum(a and b for a,b in zip(truth,pred))
    tn=sum(not a and not b for a,b in zip(truth,pred))
    fp=sum(not a and b for a,b in zip(truth,pred))
    fn=sum(a and not b for a,b in zip(truth,pred))
    def safe_ratio(n,d): return None if d==0 else n/d
    return dict(n=len(truth),tp=tp,tn=tn,fp=fp,fn=fn,
                precision=safe_ratio(tp,tp+fp),recall=safe_ratio(tp,tp+fn),
                specificity=safe_ratio(tn,tn+fp),accuracy=safe_ratio(tp+tn,len(truth)),
                false_negative_rate=safe_ratio(fn,fn+tp),
                scope="Evaluation on supplied labels; no industrial certification")
