import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from glass_perception.core import Detection, TemporalGate, clean, label_map
from glass_perception.backend import YoloBackend


def detection(confidence=.9, box=(10., 10., 30., 40.)):
    return Detection('suspect_surface', confidence, box)


class GateTests(unittest.TestCase):
    def test_requires_three_observations(self):
        gate = TemporalGate()
        rows = [gate.update([detection()], t, 100, 100)[0] for t in (1., 1.1, 1.2)]
        self.assertEqual([r['stable'] for r in rows], [False, False, True])
        self.assertEqual(len({r['track_id'] for r in rows}), 1)

    def test_empty_frame_does_not_publish_ghost(self):
        gate = TemporalGate(min_hits=1)
        gate.update([detection()], 1., 100, 100)
        self.assertEqual(gate.update([], 1.1, 100, 100), [])

    def test_miss_breaks_consecutive_hits(self):
        gate = TemporalGate()
        gate.update([detection()], 1., 100, 100)
        gate.update([], 1.1, 100, 100)
        row = gate.update([detection()], 1.2, 100, 100)[0]
        self.assertEqual(row['consecutive_hits'], 1)
        self.assertFalse(row['stable'])

    def test_expiration_assigns_new_id(self):
        gate = TemporalGate()
        a = gate.update([detection()], 1., 100, 100)[0]
        b = gate.update([detection()], 2., 100, 100)[0]
        self.assertNotEqual(a['track_id'], b['track_id'])

    def test_weak_persistent_candidate_not_stable(self):
        gate = TemporalGate()
        for stamp in (1., 1.1, 1.2, 1.3):
            self.assertFalse(gate.update([detection(.3)], stamp, 100, 100)[0]['stable'])

    def test_rejects_repeated_and_reversed_stamps_without_mutation(self):
        gate = TemporalGate()
        gate.update([detection()], 2., 100, 100)
        for stamp in (2., 1., float('nan'), -1.):
            with self.assertRaises(ValueError):
                gate.update([detection()], stamp, 100, 100)
        self.assertEqual(gate.update([detection()], 2.1, 100, 100)[0]['consecutive_hits'], 2)

    def test_invalid_box_does_not_consume_timestamp(self):
        gate = TemporalGate()
        with self.assertRaises(ValueError):
            gate.update([detection(box=(20, 0, 10, 30))], 1., 100, 100)
        self.assertEqual(gate.update([detection()], 1., 100, 100)[0]['consecutive_hits'], 1)

    def test_one_to_one_association_independent_of_order(self):
        gate = TemporalGate()
        a, b = detection(), detection(box=(60., 10., 90., 40.))
        first = gate.update([a, b], 1., 100, 100)
        second = gate.update([b, a], 1.1, 100, 100)
        self.assertEqual(first[0]['track_id'], second[1]['track_id'])
        self.assertEqual(first[1]['track_id'], second[0]['track_id'])

    def test_large_motion_does_not_invent_identity(self):
        gate = TemporalGate()
        a = gate.update([detection()], 1., 100, 100)[0]
        b = gate.update([detection(box=(60, 60, 90, 90))], 1.1, 100, 100)[0]
        self.assertNotEqual(a['track_id'], b['track_id'])

    def test_clips_pixel_geometry(self):
        row = clean(Detection('suspect_surface', .8, (-5, -5, 200, 200),
                              ((-1, -2), (20, 0), (200, 200))), 100, 100)
        self.assertEqual(row.box, (0, 0, 100, 100))
        self.assertEqual(row.polygon[-1], (100, 100))

    def test_invalid_configuration(self):
        for options in ({'min_hits': 0}, {'window': 1}, {'ttl': float('inf')},
                        {'match_iou': 0}, {'min_mean_confidence': 1.1}):
            with self.assertRaises(ValueError):
                TemporalGate(**options)

    def test_invalid_image_dimensions_even_when_empty(self):
        with self.assertRaises(ValueError):
            TemporalGate().update([], 1., 0, 100)

    def test_nonfinite_and_zero_area_detections(self):
        for d in (detection(float('nan')), detection(1.1), detection(box=(0,0,0,10)),
                  detection(box=(0,0,float('inf'),10))):
            with self.assertRaises(ValueError):
                clean(d, 100, 100)

    def test_single_class_weights(self):
        self.assertEqual(label_map({0: 'suspect_surface'}, ['suspect_surface']), {0: 'suspect_surface'})

    def test_existing_material_model_collapses_to_one_candidate_type(self):
        self.assertEqual(label_map({0:'glass',1:'mirror',2:'person'}, ['glass','mirror']),
                         {0:'suspect_surface',1:'suspect_surface'})

    def test_generic_model_cannot_silently_be_used(self):
        with self.assertRaises(ValueError):
            label_map({0:'person',1:'car'}, ['suspect_surface'])

    def test_missing_weights_fails_before_importing_torch(self):
        with self.assertRaises(ValueError):
            YoloBackend('', ['suspect_surface'])


if __name__ == '__main__':
    unittest.main()
