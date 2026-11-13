import {
  ACESFilmicToneMapping, DirectionalLight, HemisphereLight, MathUtils, PCFShadowMap, PMREMGenerator, Scene, Vector3,
} from 'three'
import type { WebGLRenderer } from 'three'
import { Sky } from 'three/addons/objects/Sky.js'

const TAILLE_OMBRES = 2048
const PORTEE_OMBRES = 14
const RECUL_DU_SOLEIL = 60

export type Eclairer = (position: Vector3) => void

export function installerCiel(scene: Scene, renderer: WebGLRenderer): Eclairer {
  const sky = new Sky()
  sky.scale.setScalar(10000)
  const soleil = new Vector3().setFromSphericalCoords(1, MathUtils.degToRad(52), MathUtils.degToRad(140))
  const reglages = sky.material.uniforms
  reglages['turbidity']!.value = 4
  reglages['rayleigh']!.value = 1.2
  reglages['mieCoefficient']!.value = 0.004
  reglages['mieDirectionalG']!.value = 0.8
  reglages['sunPosition']!.value.copy(soleil)
  renderer.toneMapping = ACESFilmicToneMapping
  renderer.toneMappingExposure = 0.6

  const reflets = new PMREMGenerator(renderer)
  const sceneDuCiel = new Scene()
  sceneDuCiel.add(sky)
  scene.environment = reflets.fromScene(sceneDuCiel, 0, 1, 20000).texture
  scene.environmentIntensity = 0.12
  reflets.dispose()
  scene.add(sky)

  const lumiere = new DirectionalLight(0xfff0d6, 2.6)
  lumiere.castShadow = true
  lumiere.shadow.mapSize.set(TAILLE_OMBRES, TAILLE_OMBRES)
  const zone = lumiere.shadow.camera
  zone.left = zone.bottom = -PORTEE_OMBRES
  zone.right = zone.top = PORTEE_OMBRES
  zone.near = 1
  zone.far = 2 * RECUL_DU_SOLEIL
  lumiere.shadow.bias = -0.0004
  lumiere.shadow.normalBias = 0.02
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = PCFShadowMap
  scene.add(new HemisphereLight(0xcfe6ff, 0x4a6b2a, 1.1), lumiere, lumiere.target)

  return (position) => {
    lumiere.target.position.copy(position)
    lumiere.position.copy(position).addScaledVector(soleil, RECUL_DU_SOLEIL)
  }
}
