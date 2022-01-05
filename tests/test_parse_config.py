import importlib

import pytest
from mock import patch, Mock, call

import datman.config

pc = importlib.import_module('bin.parse_config')


class TestPromptUser:

    @patch('builtins.input')
    def test_true_only_when_y_given(self, mock_input):
        user_input = [
            '         ',
            '',
            'y',
            'n',
        ]

        mock_input.side_effect = lambda x: user_input.pop()

        assert pc.prompt_user('Test message') is False
        assert pc.prompt_user('Test message') is True
        assert pc.prompt_user('Test message') is False
        assert pc.prompt_user('Test message') is False

    @patch('builtins.input')
    def test_raises_runtime_error_for_unexpected_response(self, mock_input):
        mock_input.return_value = 'dfgsxcvqa'
        with pytest.raises(RuntimeError):
            pc.prompt_user('Test message')


class TestUpdateTags:

    @patch('dashboard.queries.get_scantypes')
    def test_tag_created_in_database_if_doesnt_exist(self, mock_db_tags):
        config = self.get_config()
        pc.update_tags(config)
        assert call('T1', create=True) in mock_db_tags.call_args_list

    @patch('dashboard.queries.get_scantypes')
    def test_existing_tag_updated_when_settings_changed(self, mock_db_tags):
        config = self.get_config()

        db_tag = Mock()
        db_tag.tag = 'T1'
        db_tag.qc_type = 'func'
        db_tag.pha_type = 'func'
        existing_tags = [db_tag]

        mock_db_tags.side_effect = self.get_scantype_func(existing_tags)

        pc.update_tags(config)

        assert len(existing_tags) == 1
        db_tag = existing_tags[0]
        assert db_tag.tag == 'T1'
        assert db_tag.qc_type == 'anat'
        assert db_tag.pha_type is None

    @patch('bin.parse_config.delete_records')
    @patch('dashboard.queries.get_scantypes')
    def test_calls_delete_records_if_undefined_tags_exist(
            self, mock_db_tags, mock_delete):
        config = self.get_config()

        bad_tag = Mock()
        bad_tag.tag = 'T2'
        expected_tag = Mock()
        expected_tag.tag = 'T1'
        existing_tags = [bad_tag, expected_tag]

        mock_db_tags.side_effect = self.get_scantype_func(existing_tags)

        pc.update_tags(config)

        assert mock_delete.call_count == 1
        assert mock_delete.call_args[0] == ([bad_tag],)

    def get_config(self):
        def get_key(name):
            if name == 'ExportSettings':
                return {
                            'T1': {
                                'Formats': ['nii', 'dcm', 'mnc'],
                                'QcType': 'anat'
                            },
                        }
            raise datman.config.UndefinedSetting

        config = Mock(spec=datman.config.config)
        config.get_key = get_key

        return config

    def get_scantype_func(self, existing_tags):
        # Provide a mock dashboard.queries.get_scantypes interface
        # with 'existing_tags' as the fake records.
        def get_scantype(tag=None, create=False):
            if not tag:
                return existing_tags

            found = [item for item in existing_tags if item.tag == tag]
            if not found and create:
                new_tag = Mock()
                new_tag.tag = tag
                existing_tags.append(new_tag)
                return [new_tag]

            return found
        return get_scantype


class TestDeleteRecords:

    def test_nothing_deleted_when_skip_delete_flag_set(self):
        records = self.get_mock_records()
        pc.delete_records(records, skip_delete=True)
        for item in records:
            assert item.delete.call_count == 0

    def test_all_given_records_deleted_when_delete_all_set(self):
        records = self.get_mock_records()
        pc.delete_records(records, delete_all=True)
        for item in records:
            assert item.delete.call_count == 1

    @patch('builtins.input')
    def test_delete_func_used_to_delete_when_provided(self, mock_input):
        mock_input.return_value = 'y'
        def delete_func(x):
            x.alt_delete()
        records = self.get_mock_records()
        pc.delete_records(records, delete_func=delete_func)

        for item in records:
            assert item.delete.call_count == 0

        for item in records:
            assert item.alt_delete.call_count == 1

    @patch('builtins.input')
    @patch('bin.parse_config.prompt_user')
    def test_prompt_changed_when_flag_set(self, mock_prompt, mock_input):
        mock_input.return_value = 'y'
        records = self.get_mock_records()

        message = 'Testing prompt flag'
        pc.delete_records(records, prompt=message)
        for call in mock_prompt.call_args_list:
            assert message in call.args[0]

    @patch('builtins.input')
    def test_records_only_deleted_when_user_consents(self, mock_input):
        responses = ['n', 'n', 'y', 'n']
        mock_input.side_effect = lambda x: responses.pop()
        records = self.get_mock_records()

        pc.delete_records(records)

        assert records[0].delete.call_count == 0
        assert records[1].delete.call_count == 1
        assert records[2].delete.call_count == 0
        assert records[3].delete.call_count == 0

    def get_mock_records(self):
        records = []
        for _ in range(4):
            records.append(Mock())
        return records


class TestUpdateExpectedScans:

    def test_no_crash_if_site_undefined_in_config(self, config):
        pc.update_expected_scans(Mock(), 'BADSITE', config)

    def test_no_crash_if_no_scans_defined_for_site(self, config):
        mock_study = Mock()
        mock_study.scantypes = {}
        pc.update_expected_scans(mock_study, 'NOSCANS', config)

    def test_no_scantypes_added_if_none_defined_in_config(self, config):
        mock_study = Mock()
        mock_study.scantypes = {}

        pc.update_expected_scans(mock_study, 'NOSCANS', config)
        assert mock_study.update_scantype.call_count == 0

    @patch('bin.parse_config.delete_records')
    def test_attempts_to_delete_database_scantypes_if_not_in_config(self,
            mock_delete, config):
        mock_study = Mock()
        mock_t1 = Mock()
        mock_t1.scantype_id = 'T1'
        mock_t2 = Mock()
        mock_t2.scantype_id = 'T2'
        mock_study.scantypes = {
            'SITE': [mock_t1, mock_t2]
        }

        pc.update_expected_scans(mock_study, 'SITE', config)
        assert mock_delete.call_count == 1
        assert mock_delete.call_args_list[0].args[0][0] == mock_t2

    def test_expected_tags_updated_in_database(self, config):
        mock_t1 = Mock()
        mock_t1.scantype_id = 'T1'
        mock_study = Mock()
        mock_study.scantypes = {
            'SITE': [mock_t1]
        }

        pc.update_expected_scans(mock_study, 'SITE', config)
        assert mock_study.update_scantype.call_count == 1
        assert mock_study.update_scantype.call_args_list[0][0][1] == 'T1'

    @pytest.fixture
    def config(self):
        tag_settings = {
            'T1': {
                'formats': ['nii', 'dcm', 'mnc'],
                'qc_type': 'anat',
                'bids': {'class': 'anat', 'modality_label': 'T1w'},
                'Pattern': {'SeriesDescription': ['T1', 'BRAVO']},
                'Count': 1
            }
        }

        def get_tags(name):
            if name == 'SITE':
                return datman.config.TagInfo(tag_settings)
            if name == 'NOSCANS':
                return datman.config.TagInfo({})
            raise datman.config.UndefinedSetting

        config = Mock(spec=datman.config.config)
        config.get_tags.side_effect = get_tags

        return config


class TestUpdateSite:

    @patch('bin.parse_config.update_expected_scans')
    def test_no_crash_with_undefined_settings(self, mock_expected, config):
        pc.update_site(Mock(), 'CMH', config)

    def test_raises_exception_when_given_undefined_site(self, config):
        with pytest.raises(Exception):
            pc.update_site(Mock(), 'BADSITE', config)

    @patch('bin.parse_config.update_expected_scans')
    def test_study_record_updated_for_given_site(self, mock_expected, config):
        mock_study = Mock()
        pc.update_site(mock_study, 'CMH', config)

        assert mock_study.update_site.call_count == 1
        assert mock_study.update_site.call_args_list[0][0][0] == 'CMH'

    @patch('bin.parse_config.update_expected_scans')
    def test_expected_scans_updated_for_site(self, mock_expected, config):
        mock_study = Mock()
        pc.update_site(mock_study, 'CMH', config)

        mock_expected.assert_called_once_with(
            mock_study, 'CMH', config, False, False
        )

    @pytest.fixture
    def config(self):
        sites = {
            'CMH': {
                'STUDY_TAG': 'TST01'
            }
        }
        def get_key(key, site=None):
            if not site:
                raise datman.config.UndefinedSetting
            try:
                site_conf = sites[site]
            except KeyError:
                raise datman.config.ConfigException
            try:
                return site_conf[key]
            except KeyError:
                raise datman.config.UndefinedSetting

        config = Mock(spec=datman.config.config)
        config.get_key = get_key
        return config


class TestUpdateStudy:

    def test_no_crash_when_study_undefined(self):
        config = Mock(spec=datman.config.config)
        def set_study(study):
            raise datman.config.ConfigException
        config.set_study = set_study
        pc.update_study("BADSTUDY", config)

    @patch('dashboard.queries')
    def test_no_crash_when_sites_not_defined(self, mock_dash):
        config = Mock(spec=datman.config.config)
        def get_sites():
            raise datman.config.UndefinedSetting
        config.get_sites = get_sites
        pc.update_study('STUDY', config)

    @patch('bin.parse_config.update_expected_scans')
    @patch('builtins.input')
    @patch('dashboard.queries')
    def test_site_records_deleted_if_no_longer_in_config(
            self, mock_dash, mock_input, mock_expected, config):
        mock_input.return_value = 'y'

        mock_study = Mock()
        mock_study.sites = {
            'CMH': Mock(),
            'UTO': Mock()
        }
        def get_studies(study, create=False):
            return [mock_study] if study == 'STUDY' else []
        mock_dash.get_studies = get_studies

        pc.update_study('STUDY', config)
        mock_study.delete_site.assert_called_once_with('UTO')


    @patch('bin.parse_config.update_site')
    @patch('bin.parse_config.delete_records')
    @patch('dashboard.queries')
    def test_update_site_called_for_each_site_in_config(
            self, mock_dash, mock_delete, mock_update_site):
        mock_study = Mock()
        mock_study.sites = {
            'CMH': Mock(),
            'UTO': Mock()
        }
        mock_dash.get_studies.return_value = [mock_study]

        config = Mock(spec=datman.config.config)
        config.get_key.return_value = False
        config.get_sites.return_value = ['CMH']

        pc.update_study('STUDY', config)
        mock_update_site.assert_called_once_with(
            mock_study, 'CMH', config, delete_all=False, skip_delete=False
        )

    @pytest.fixture
    def config(self):
        def get_key(key, site=None, ignore_defaults=False,
                    defaults_only=False):
            try:
                return {}[key]
            except:
                raise datman.config.UndefinedSetting

        config = Mock(spec=datman.config.config)
        config.get_key.side_effect = get_key

        def get_path(path, study=None):
            try:
                return {}[path]
            except:
                raise datman.config.UndefinedSetting

        config.get_sites.return_value = ['CMH']

        return config


@patch('dashboard.queries')
@patch('bin.parse_config.delete_records')
@patch('bin.parse_config.update_study')
class TestUpdateStudies:

    def test_no_crash_when_studies_not_defined(self, mock_update, mock_delete,
                mock_dash):
        config = Mock(spec=datman.config.config)
        def get_key(key):
            raise datman.config.UndefinedSetting
        config.get_key = get_key

        pc.update_studies(config)

    def test_creates_or_updates_each_study_found_in_config(self, mock_update,
                mock_delete, mock_dash, config):
        mock_dash.get_projects.return_value = []
        pc.update_studies(config)
        assert mock_update.call_count == len(config.get_key('Projects').keys())

    def test_deletes_studies_not_defined_in_config(self, mock_update,
                mock_delete, mock_dash, config):
        mock_study = Mock()
        mock_study.id = 'STUDY5'
        mock_dash.get_studies.return_value = [mock_study]

        pc.update_studies(config, delete_all=True)
        assert mock_delete.call_count == 1
        assert mock_delete.call_args_list[0][0][0] == [mock_study]

    @pytest.fixture
    def config(self, *args):
        config = Mock(spec=datman.config.config)
        config.get_key.side_effect = lambda x: {
            'Projects': {
                'STUDY1',
                'STUDY2',
                'STUDY3'
            }
        }
        return config
