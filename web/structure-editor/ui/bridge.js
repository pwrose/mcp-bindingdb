import { App } from '@modelcontextprotocol/ext-apps';
window.BindingDBHost = null;
if (window.parent !== window) {
  const app = new App({name:'BindingDB Structure Studio',version:'1.0.0'}, {}, {autoResize:true});
  let reported = null;
  app.ontoolresult = result => {
    let data = result.structuredContent;
    if (!data) { try { data = JSON.parse(result.content?.find(c=>c.type==='text')?.text || '{}'); } catch {} }
    if (data && Object.hasOwn(data,'initial_query')) { window.BindingDBInitialData=data; window.dispatchEvent(new CustomEvent('bindingdb-initial', {detail:data})); }
    // Tells the server this editor appeared: a chat app may show no panel for a call, and only the page knows.
    if (data?.editor_id && data.editor_id !== reported) {
      reported = data.editor_id;
      connected.then(()=>app.callServerTool({name:'editor_opened', arguments:{editor_id:data.editor_id}})).catch(()=>{});
    }
  };
  const connected = app.connect();
  connected.then(()=>{ window.BindingDBHost=app; window.dispatchEvent(new Event('bindingdb-connected')); }).catch(()=>{});
}
