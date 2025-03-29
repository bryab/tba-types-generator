/**
 *  The properties of this interface are not documented in full (FIXME)
 * {@link https://docs.toonboom.com/help/harmony-24/scripting/extended/module-Drawing_Text_.html}
 */
declare interface TextLayer {
  id?: number;
  text?: string;
  fontsize?: number;
  x?: number;
  y?: number;
  colorId?: number;
  fontId?: string;
  alignment: string;
  colorMatrix?: object;
  width?: number;
  underLayer?: number;
}

//Unknown types in Harmony 24
type TUSceneChangeManager = any;

// A few Qt6 types referenced in the documentation - Qt defs are currently based on Qt4

type QProcessEnvironment = any;
