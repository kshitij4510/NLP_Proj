import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { projectsApi, reportsApi } from "@/api/endpoints";
import { errorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/button";
import type { Report } from "@/types";
type SourceFinding = {kind:string; evidence:string; change:string; page?:number|null; source_file?:string|null; basis?:string};
type ReviewCheck = {topic:string; status:string; evidence:string; page?:number|null; source_file?:string|null; note:string};

export default function ManuscriptStudio({ projectId, paperOnly=false, onReport, onProjectCreated }: {projectId:string; paperOnly?:boolean; onReport?:(r:Report)=>void; onProjectCreated?:(id:string)=>void}) {
 const [file,setFile]=useState<File|null>(null),[github,setGithub]=useState(""),[title,setTitle]=useState("");
 const [author,setAuthor]=useState(""),[affiliation,setAffiliation]=useState("");
 const qc=useQueryClient();
 const [createdProjectId,setCreatedProjectId]=useState("");
 const review=useMutation({mutationFn:async()=>{
   let targetProjectId=projectId||createdProjectId;
   if(!targetProjectId){
     const project=await projectsApi.create({title:(title.trim()||file?.name.replace(/\.[^.]+$/, "")||github.trim().split("/").pop()||"Source review").slice(0,200)});
     targetProjectId=project.id;
     setCreatedProjectId(project.id);
     onProjectCreated?.(project.id);
     qc.invalidateQueries({queryKey:["projects"]});
   }
   const form=new FormData();if(file)form.append("file",file);else form.append("github_url",github.trim());form.append("title",title);form.append("author",author);form.append("affiliation",affiliation);
   const data=(await apiClient.post<{report:Report;gaps:SourceFinding[];review_checks:ReviewCheck[];mode:string}>(`/projects/${targetProjectId}/manuscripts`,form,{headers:{"Content-Type":"multipart/form-data"},timeout:180000})).data;
   return {...data,projectId:targetProjectId};
 },onSuccess:(data)=>{qc.invalidateQueries();onReport?.(data.report);}});
 const download=useMutation({mutationFn:(format:"ieee"|"markdown"|"bibtex")=>reportsApi.download(review.data!.projectId,review.data!.report.id,format)});
 const {data:reviewResult,isPending:reviewPending,reset:resetReview}=review;
 useEffect(()=>{
   if(reviewResult && projectId && reviewResult.projectId!==projectId && !reviewPending) resetReview();
 },[projectId,reviewResult,reviewPending,resetReview]);
 return <section className="source-studio border p-6 space-y-4 bg-card">
 <div><p className="text-xs uppercase tracking-widest text-muted-foreground">{paperOnly?"Paper review":"Manuscript desk"}</p><h2 className="text-2xl editorial-title">{paperOnly?"Find gaps in your paper":"Turn your project into a research draft"}</h2><p className="text-sm text-muted-foreground mt-2">{paperOnly?"Upload a searchable PDF. Review the gaps and proposed changes, then export an IEEE revision draft.":"Upload a project ZIP, PDF, Markdown, or source file, or enter a public GitHub repository. Source files are inspected; code is never executed."}</p></div>
 <label className="block text-sm">Manuscript title<input className="block border bg-background p-2 w-full mt-1" value={title} onChange={e=>setTitle(e.target.value)} placeholder="Optional title" maxLength={400}/></label>
 <div className="grid sm:grid-cols-2 gap-4"><label className="text-sm">Authors<input className="block border bg-background p-2 w-full mt-1" placeholder="Author names" value={author} maxLength={300} onChange={e=>setAuthor(e.target.value)}/></label><label className="text-sm">Affiliation<input className="block border bg-background p-2 w-full mt-1" placeholder="Institution or organization" value={affiliation} maxLength={500} onChange={e=>setAffiliation(e.target.value)}/></label></div>
 <label className="block text-sm">{paperOnly?"Paper PDF":"Project or paper file"}<input type="file" className="block mt-2 text-sm" accept={paperOnly?".pdf":".pdf,.zip,.md,.txt,.py,.js,.ts,.tsx,.json,.yaml,.yml,.toml,.tex,.csv"} onChange={e=>{setFile(e.target.files?.[0]||null);setGithub("");review.reset();}}/></label>
 {!paperOnly&&<label className="block text-sm">Or public GitHub repository<input className="block border bg-background p-2 w-full mt-1" placeholder="https://github.com/owner/repository" value={github} disabled={!!file} onChange={e=>{setGithub(e.target.value);review.reset();}}/>{file&&<button className="underline text-xs mt-1" onClick={()=>setFile(null)}>Use a GitHub link instead</button>}</label>}
 <Button disabled={(!file&&!github.trim())||review.isPending} onClick={()=>review.mutate()}>{review.isPending?"Reading source and preparing draft…":paperOnly?"Analyze paper and prepare revision":"Analyze source and write draft"}</Button>
 {!projectId&&!createdProjectId&&<p className="text-sm">Choose a file to analyze. A project will be created automatically, or select an existing project above.</p>}
 {(review.error||download.error)&&<p role="alert" className="text-destructive">{errorMessage(review.error||download.error)}</p>}
 {review.data&&<div className="space-y-4 border-t pt-4">
   <p className="text-sm">{review.data.mode==="extractive"?"Local source-based draft":"Synthesized draft"}. Findings are text-based review candidates, not validated research gaps. Proposed changes are not implemented or experimentally validated.</p>
   <h3 className="font-semibold">Source statements and review suggestions</h3>
   <p className="text-sm text-muted-foreground">Author-stated future work is an existing proposal in the source, not a new gap discovered by this app. Page numbers refer to PDF pages.</p>
   {review.data.gaps.length===0?<p>No explicit limitation or future-work statements located. Manual review is still required.</p>:review.data.gaps.map((g,i)=><article key={i} className="border-l-2 pl-4 space-y-2">
     <h4 className="font-medium">{g.kind}</h4>
     {(g.page||g.source_file)&&<p className="text-xs text-muted-foreground">{g.page?`PDF page ${g.page}`:g.source_file}</p>}
     <blockquote className="text-sm text-muted-foreground whitespace-pre-wrap">{g.evidence}</blockquote>
     <p className="text-sm"><strong>Suggested follow-up: </strong>{g.change}</p>
     {g.basis&&<p className="text-xs text-muted-foreground">{g.basis}</p>}
   </article>)}
   {!!review.data.review_checks?.length&&<div className="space-y-3 border-t pt-4">
     <h3 className="font-semibold">Documentation checks</h3>
     <p className="text-sm text-muted-foreground">A located mention does not establish completeness. A missing match does not establish absence.</p>
     {review.data.review_checks.map(check=><article key={check.topic} className="border p-3 space-y-2">
       <h4 className="font-medium">{check.topic}: {check.status}</h4>
       {(check.page||check.source_file)&&<p className="text-xs text-muted-foreground">{check.page?`PDF page ${check.page}`:check.source_file}</p>}
       <p className="text-sm text-muted-foreground">{check.evidence}</p>
       <p className="text-xs text-muted-foreground">{check.note}</p>
     </article>)}
   </div>}
   <div className="flex flex-wrap gap-2">{(["ieee","markdown","bibtex"] as const).map(f=><Button key={f} variant="outline" disabled={download.isPending} onClick={()=>download.mutate(f)}>{f==="ieee"?"IEEE manuscript (.tex)":f==="bibtex"?"References (.bib)":"Manuscript (.md)"}</Button>)}</div>
   <p className="text-xs text-muted-foreground">Compile .tex with IEEEtran in Overleaf. References are selected from the uploaded paper and matching corpus records. A draft with no matching sources has an empty .bib.</p>
 </div>}
 </section>;
}
