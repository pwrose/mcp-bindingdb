import { App } from '@modelcontextprotocol/ext-apps';
// Shows the image a figure tool (draw_structure_grid) returns in the chat, where a host would otherwise show only
// a thumbnail. Hosts may strip the image from the result they give the panel; then it fetches the saved file.
const status = document.getElementById('status'), figure = document.getElementById('figure');
const app = new App({name:'BindingDB Figure',version:'1.0.0'}, {}, {autoResize:true});
const show = (mimeType, data) => { figure.src = 'data:' + mimeType + ';base64,' + data; figure.hidden = false; status.hidden = true; };
const text = result => result.content?.find(c => c.type === 'text')?.text;
app.ontoolresult = async result => {
  if (result.isError) { status.textContent = text(result) || 'The figure could not be drawn.'; return; }
  const image = result.content?.find(c => c.type === 'image');
  if (image) return show(image.mimeType, image.data);
  const file = result.structuredContent?.figure_file;
  if (!file) { status.textContent = 'This result has no saved figure.'; return; }
  try {
    const saved = await app.callServerTool({name:'figure_image', arguments:{file}});
    if (saved.isError) throw new Error(text(saved));
    show(saved.structuredContent.mime_type, saved.structuredContent.data);
  } catch (e) { status.textContent = 'Could not load the figure: ' + (e.message || e); }
};
// The automatic size report may come before the image has loaded; report the final height too.
figure.onload = () => app.sendSizeChanged({width: Math.ceil(window.innerWidth), height: Math.ceil(document.documentElement.getBoundingClientRect().height)});
app.connect().catch(() => { status.textContent = 'Open this figure in an MCP Apps chat client.'; });
