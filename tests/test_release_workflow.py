"""Forks can build audited firmware without publishing an unsigned release."""
from pathlib import Path
import re
import unittest

TOP = Path(__file__).resolve().parents[1]


class ReleaseWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (TOP / '.github/workflows/release.yml').read_text(encoding='utf-8')

    def test_publishing_is_an_explicit_boolean_opt_in(self):
        self.assertRegex(self.workflow,
                         r'(?m)^      publish:\n(?:        [^\n]*\n)*?'
                         r'        type: boolean\n        default: false\n')
        self.assertIn('INPUT_PUBLISH: ${{ inputs.publish }}', self.workflow)
        self.assertIn('[ "$INPUT_PUBLISH" != true ] || set -- "$@" --publish', self.workflow)
        self.assertIn('sudo -E sh tools/make-release.sh "$@"', self.workflow)
        self.assertNotIn('"$TAG" --publish --any-date', self.workflow)

    def test_publishing_checks_the_matching_key_before_building(self):
        preflight = self.workflow.split('      - name: Check publishing key before building\n', 1)[1]
        preflight = preflight.split('      # the tag:', 1)[0]
        self.assertIn('        if: inputs.publish\n', preflight)
        self.assertIn('MU300_RELEASE_KEY: ${{ secrets.MU300_RELEASE_KEY }}', preflight)
        self.assertIn('sh tools/sign-release.sh "$check/SHA256SUMS" '
                      'rootfs/overlay/opt/mu300/lib/release.pub', preflight)
        self.assertLess(self.workflow.index('Check publishing key before building'),
                        self.workflow.index('Vendor 5.4 kernel and modules'))

    def test_artifact_upload_excludes_staged_inputs_and_limits_retention(self):
        artifact = self.workflow.split('      - name: Firmware build artifacts\n', 1)[1]
        artifact = artifact.split('      - name: Magisk installers\n', 1)[0]
        self.assertIn('uses: actions/upload-artifact@v4', artifact)
        paths = re.findall(r'^            (release/[^\n]+)', artifact, flags=re.MULTILINE)
        self.assertEqual(paths, [
            'release/${{ env.TAG }}/*.tar.gz',
            'release/${{ env.TAG }}/*.manifest.gz',
            'release/${{ env.TAG }}/SHA256SUMS*',
            'release/${{ env.TAG }}/mu300-update',
            'release/${{ env.TAG }}/mu300-release',
        ])
        self.assertIn('if-no-files-found: error', artifact)
        self.assertIn('retention-days: 7', artifact)

    def test_build_only_does_not_dispatch_magisk_installers(self):
        magisk = self.workflow.split('      - name: Magisk installers\n', 1)[1]
        self.assertIn('        if: inputs.publish\n', magisk)
        self.assertIn('gh workflow run magisk.yml', magisk)


if __name__ == '__main__':
    unittest.main()
