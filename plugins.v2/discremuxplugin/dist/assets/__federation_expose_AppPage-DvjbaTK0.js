import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Page from './__federation_expose_Page-D-YC-d2G.js';

const {openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: { type: Object, required: true },
},
  setup(__props) {

const props = __props;

return (_ctx, _cache) => {
  return (_openBlock(), _createBlock(Page, {
    api: props.api
  }, null, 8, ["api"]))
}
}

};

export { _sfc_main as default };
