import subprocess,difflib,sys,re
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384'
files=subprocess.check_output(['git','-C',W,'diff','--name-only','07181524','c9340f8b']).decode().split()
out=open('segments.txt','w',encoding='utf-8')
for f in files:
    a=subprocess.check_output(['git','-C',W,'show','07181524:'+f]).decode('utf-8').splitlines()
    b=subprocess.check_output(['git','-C',W,'show','c9340f8b:'+f]).decode('utf-8').splitlines()
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal':continue
        out.write(f'\n######## {f} {tag} old {i1+1}-{i2} new {j1+1}-{j2}\n')
        # pair lines
        for k in range(max(i2-i1,j2-j1)):
            ol=a[i1+k] if i1+k<i2 else ''
            nl=b[j1+k] if j1+k<j2 else ''
            ow=re.split(r'(\s+)',ol); nw=re.split(r'(\s+)',nl)
            s2=difflib.SequenceMatcher(None,ow,nw,autojunk=False)
            out.write(f'--- line new {j1+k+1} (len old {len(ol)} new {len(nl)})\n')
            for t,x1,x2,y1,y2 in s2.get_opcodes():
                if t=='equal':
                    seg=''.join(ow[x1:x2])
                    if len(seg)>160: seg=seg[:70]+' ... '+seg[-70:]
                    out.write(seg)
                else:
                    out.write('[-'+''.join(ow[x1:x2])+'-]{+'+''.join(nw[y1:y2])+'+}')
            out.write('\n')
