import { App } from '@modelcontextprotocol/ext-apps';
window.BindingDBHost = null;
if (window.parent !== window) {
  const app = new App({name:'BindingDB Structure Studio',version:'1.0.0'}, {}, {autoResize:true});
  app.ontoolresult = result => {
    let data = result.structuredContent;
    if (!data) { try { data = JSON.parse(result.content?.find(c=>c.type==='text')?.text || '{}'); } catch {} }
    if (data && Object.hasOwn(data,'initial_query')) { window.BindingDBInitialData=data; window.dispatchEvent(new CustomEvent('bindingdb-initial', {detail:data})); }
  };
  app.connect().then(()=>{ window.BindingDBHost=app; window.dispatchEvent(new Event('bindingdb-connected')); }).catch(()=>{});
}
