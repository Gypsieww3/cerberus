"""Reference difference inspection for aligned 8-bit grayscale arrays, offline only."""
import math


def validate(image):
    if not image or not image[0]:raise ValueError('Empty image')
    width=len(image[0])
    if len(image)*width>1_000_000:raise ValueError('Pixel limit exceeded')
    if any(len(row)!=width for row in image):raise ValueError('Ragged image')
    if any(type(v) is not int or not 0<=v<=255 for row in image for v in row):raise ValueError('Use 8-bit grayscale integers')
    return width,len(image)


def inspect(reference,sample,threshold=30,min_area=3,max_mean_shift=10):
    width,height=validate(reference)
    if validate(sample)!=(width,height):raise ValueError('Image dimensions differ')
    if type(threshold) is not int or not 0<=threshold<=255:raise ValueError('Invalid threshold')
    if type(min_area) is not int or min_area<1:raise ValueError('Invalid area')
    if not math.isfinite(max_mean_shift) or max_mean_shift<0:raise ValueError('Invalid illumination limit')
    shift=abs(sum(v for row in reference for v in row)-sum(v for row in sample for v in row))/(width*height)
    pixels={(x,y) for y in range(height) for x in range(width) if abs(sample[y][x]-reference[y][x])>threshold}
    changed=len(pixels);components=[]
    for first in sorted(pixels,key=lambda p:(p[1],p[0])):
        if first not in pixels:continue
        pixels.remove(first);pending=[first];region=[]
        while pending:
            x,y=pending.pop();region.append((x,y))
            for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if point in pixels:pixels.remove(point);pending.append(point)
        if len(region)>=min_area:
            xs,ys=zip(*region);components.append(dict(area=len(region),bbox=[min(xs),min(ys),max(xs)+1,max(ys)+1]))
    state='REVIEW_LIGHTING' if shift>max_mean_shift else ('DEFECT_CANDIDATE' if components else 'NO_DIFFERENCE_ABOVE_LIMIT')
    return dict(state=state,mean_shift=shift,changed_pixels=changed,components=components,
                scope='Aligned synthetic/reference image comparison; no camera calibration or industrial certification')


def read_pgm(path):
    """Read bounded ASCII PGM P2 files; no image libraries or cameras required."""
    from pathlib import Path
    with Path(path).open('rb') as stream:raw=stream.read(8_000_001)
    if len(raw)>8_000_000:raise ValueError('PGM exceeds 8 MB')
    tokens=' '.join(line.split('#',1)[0] for line in raw.decode('ascii').splitlines()).split()
    if len(tokens)<4 or tokens[0]!='P2':raise ValueError('Only ASCII grayscale PGM P2 is supported')
    width,height,maximum=map(int,tokens[1:4])
    if width<1 or height<1 or width*height>1_000_000 or maximum!=255:raise ValueError('Invalid PGM dimensions or depth')
    if len(tokens)-4!=width*height:raise ValueError('PGM pixel count mismatch')
    pixels=list(map(int,tokens[4:]));image=[pixels[i:i+width] for i in range(0,len(pixels),width)]
    validate(image);return image
